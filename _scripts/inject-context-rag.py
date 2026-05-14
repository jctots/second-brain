#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — RAG passive surfacing.
# Every turn: embeds user message → queries Qdrant top-3 files above threshold → injects titles.
# Claude judges relevance and reads files directly if the user confirms.
# Graceful degradation: outputs nothing if Ollama/Qdrant is unconfigured or unreachable.
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

COLLECTION = "second_brain"
EMBED_MODEL = "embeddinggemma:latest"
QUERY_LIMIT = 10
MAX_FILES = 3
SCORE_THRESHOLD = 0.55


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

def ollama_embed(text: str, host: str, port: str, api_key: str | None) -> list[float]:
    url = f"http://{host}:{port}/api/embeddings"
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["embedding"]


# ── Qdrant ────────────────────────────────────────────────────────────────────

def qdrant_search(vector: list[float], host: str, port: str, api_key: str | None) -> list[dict]:
    url = f"http://{host}:{port}/collections/{COLLECTION}/points/search"
    payload = json.dumps({"vector": vector, "limit": QUERY_LIMIT, "with_payload": True}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("api-key", api_key)
    with urllib.request.urlopen(req) as resp:
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

    if not ollama_host or not qdrant_host or not prompt.strip():
        sys.exit(0)

    try:
        vec = ollama_embed(prompt, ollama_host, ollama_port, ollama_key)
        results = qdrant_search(vec, qdrant_host, qdrant_port, qdrant_key)
    except (urllib.error.URLError, OSError):
        sys.exit(0)

    seen: dict[str, float] = {}
    for hit in results:
        fp = hit["payload"].get("file_path", "")
        score = hit["score"]
        if score >= SCORE_THRESHOLD and (fp not in seen or score > seen[fp]):
            seen[fp] = score

    top_files = sorted(seen.items(), key=lambda x: x[1], reverse=True)[:MAX_FILES]
    if not top_files:
        sys.exit(0)

    lines = ["## Relevant vault notes"]
    for fp, _ in top_files:
        title = extract_h1(cwd / fp)
        lines.append(f"- {fp} — {title}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
