#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — RAG passive surfacing.
# Every turn: embeds user message → queries Qdrant top-3 files above threshold → injects titles.
# Claude judges relevance and reads files directly if the user confirms.
# Graceful degradation: outputs nothing if Ollama/Qdrant is unconfigured or unreachable.
# Failure notification: emits a warning on first failure; silent on repeat failures; emits recovery on restore.
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

_DEFAULTS = {
    "RAG_COLLECTION": "second_brain",
    "RAG_EMBED_MODEL": "embeddinggemma:latest",
    "RAG_QUERY_LIMIT": "10",
    "RAG_MAX_FILES": "3",
    "RAG_SCORE_THRESHOLD": "0.30",
    "RAG_TIMEOUT": "5",
}

_STATUS_FILE = ".rag-status"


# ── env ───────────────────────────────────────────────────────────────────────

def load_dotenv(root: Path) -> None:
    env_file = root / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


# ── Ollama ────────────────────────────────────────────────────────────────────

def ollama_embed(text: str, host: str, port: str, api_key: str | None, model: str, timeout: int) -> list[float]:
    url = f"http://{host}:{port}/api/embeddings"
    payload = json.dumps({"model": model, "prompt": text}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)["embedding"]


# ── Qdrant ────────────────────────────────────────────────────────────────────

def qdrant_search(vector: list[float], host: str, port: str, api_key: str | None, collection: str, limit: int, timeout: int) -> list[dict]:
    url = f"http://{host}:{port}/collections/{collection}/points/search"
    payload = json.dumps({"vector": vector, "limit": limit, "with_payload": True}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("api-key", api_key)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)["result"]


# ── helpers ───────────────────────────────────────────────────────────────────

def extract_h1(path: Path) -> str:
    try:
        in_frontmatter = False
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            if i == 0 and line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter:
                if line.strip() == "---":
                    in_frontmatter = False
                continue
            if line.startswith("# "):
                return line[2:].strip()
            if i > 30:
                break
    except (OSError, UnicodeDecodeError):
        pass
    return path.stem


# ── status sentinel ───────────────────────────────────────────────────────────

def read_status(cwd: Path) -> tuple[str, str, str]:
    """Returns (state, timestamp, reason). state is 'ok', 'error', or 'unknown'."""
    try:
        content = (cwd / _STATUS_FILE).read_text(encoding="utf-8").strip()
        parts = content.split("|", 2)
        if parts[0] == "error" and len(parts) == 3:
            return "error", parts[1], parts[2]
        if parts[0] == "ok":
            return "ok", "", ""
    except (OSError, ValueError):
        pass
    return "unknown", "", ""


def write_status(cwd: Path, state: str, reason: str = "") -> None:
    try:
        if state == "ok":
            (cwd / _STATUS_FILE).write_text("ok", encoding="utf-8")
        else:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            (cwd / _STATUS_FILE).write_text(f"error|{ts}|{reason}", encoding="utf-8")
    except OSError:
        pass  # never break the hook on a write failure


# ── ntfy ──────────────────────────────────────────────────────────────────────

def ntfy_notify(base_url: str, topic: str, title: str, message: str) -> None:
    try:
        url = f"{base_url.rstrip('/')}/{topic}"
        req = urllib.request.Request(url, data=message.encode("utf-8"), method="POST")
        req.add_header("Title", title)
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # never break the hook on ntfy failure


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    try:
        hook_data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    cwd = Path(hook_data.get("cwd", "."))
    prompt = hook_data.get("prompt", "")

    load_dotenv(cwd)

    ollama_host = os.environ.get("OLLAMA_HOST", "")
    ollama_port = os.environ.get("OLLAMA_PORT", "11434")
    ollama_key = os.environ.get("OLLAMA_API_KEY") or None
    qdrant_host = os.environ.get("QDRANT_HOST", "")
    qdrant_port = os.environ.get("QDRANT_PORT", "6333")
    qdrant_key = os.environ.get("QDRANT_API_KEY") or None

    collection = os.environ.get("RAG_COLLECTION", _DEFAULTS["RAG_COLLECTION"])
    embed_model = os.environ.get("RAG_EMBED_MODEL", _DEFAULTS["RAG_EMBED_MODEL"])
    query_limit = int(os.environ.get("RAG_QUERY_LIMIT", _DEFAULTS["RAG_QUERY_LIMIT"]))
    max_files = int(os.environ.get("RAG_MAX_FILES", _DEFAULTS["RAG_MAX_FILES"]))
    score_threshold = float(os.environ.get("RAG_SCORE_THRESHOLD", _DEFAULTS["RAG_SCORE_THRESHOLD"]))
    timeout = int(os.environ.get("RAG_TIMEOUT", _DEFAULTS["RAG_TIMEOUT"]))

    ntfy_url = os.environ.get("NTFY_URL", "")
    ntfy_topic = os.environ.get("RAG_NTFY_TOPIC", "second-brain-rag")

    if not ollama_host or not qdrant_host or not prompt.strip():
        sys.exit(0)

    prev_state, prev_ts, _ = read_status(cwd)

    try:
        vec = ollama_embed(prompt, ollama_host, ollama_port, ollama_key, embed_model, timeout)
    except (urllib.error.URLError, OSError):
        reason = f"Ollama unreachable ({ollama_host}:{ollama_port})"
        if prev_state != "error":
            print(f"⚠️ RAG unavailable — {reason}. RAG results will not be surfaced until the service recovers.")
            write_status(cwd, "error", reason)
            if ntfy_url:
                ntfy_notify(ntfy_url, ntfy_topic, "⚠️ Second Brain RAG unavailable", reason)
        sys.exit(0)

    try:
        results = qdrant_search(vec, qdrant_host, qdrant_port, qdrant_key, collection, query_limit, timeout)
    except (urllib.error.URLError, OSError):
        reason = f"Qdrant unreachable ({qdrant_host}:{qdrant_port})"
        if prev_state != "error":
            print(f"⚠️ RAG unavailable — {reason}. RAG results will not be surfaced until the service recovers.")
            write_status(cwd, "error", reason)
            if ntfy_url:
                ntfy_notify(ntfy_url, ntfy_topic, "⚠️ Second Brain RAG unavailable", reason)
        sys.exit(0)

    if prev_state == "error":
        print(f"✅ RAG restored — Ollama and Qdrant reachable again (was down since {prev_ts}).")
        if ntfy_url:
            ntfy_notify(ntfy_url, ntfy_topic, "✅ Second Brain RAG restored", f"RAG restored — was down since {prev_ts}.")
    write_status(cwd, "ok")

    seen: dict[str, float] = {}
    for hit in results:
        fp = hit["payload"].get("file_path", "")
        score = hit["score"]
        if score >= score_threshold and (fp not in seen or score > seen[fp]):
            seen[fp] = score

    top_files = sorted(seen.items(), key=lambda x: x[1], reverse=True)[:max_files]
    if not top_files:
        sys.exit(0)

    lines = ["## Relevant vault notes"]
    for fp, score in top_files:
        title = extract_h1(cwd / fp)
        lines.append(f"- {fp} — {title} [{score:.2f}]")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
