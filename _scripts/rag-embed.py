#!/usr/bin/env python3
# Walk all vault .md files, chunk by heading with char-limit windows + overlap,
# embed via Ollama, upsert to Qdrant.
# Run from repo root: python _scripts/rag-embed.py
# Env vars (or .env at repo root): OLLAMA_HOST, OLLAMA_PORT, OLLAMA_API_KEY,
#                                   QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

COLLECTION = "second_brain"
EMBED_MODEL = "embeddinggemma:latest"
VECTOR_SIZE = 768

MAX_CHARS = 1200
OVERLAP_CHARS = 200
MIN_CHARS = 50
BATCH_SIZE = 50

PARA_ROOTS = {"personal", "professional", "public"}
SKIP_FILES = {"index.md", "CLAUDE.md", "_memory.md"}


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

def qdrant_req(
    method: str,
    path: str,
    body: dict | None,
    host: str,
    port: str,
    api_key: str | None,
) -> dict:
    url = f"http://{host}:{port}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("api-key", api_key)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Qdrant {method} {path} → {e.code}: {e.read().decode()}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Qdrant unreachable at {host}:{port} — {e.reason}") from e


def ensure_collection(host: str, port: str, api_key: str | None) -> None:
    try:
        qdrant_req("GET", f"/collections/{COLLECTION}", None, host, port, api_key)
        print(f"Collection '{COLLECTION}' already exists.")
    except RuntimeError:
        qdrant_req(
            "PUT",
            f"/collections/{COLLECTION}",
            {"vectors": {"size": VECTOR_SIZE, "distance": "Cosine"}},
            host,
            port,
            api_key,
        )
        print(f"Created collection '{COLLECTION}'.")


SKIP_DIRS = {"tags"}

def should_skip(rel: Path) -> bool:
    parts = rel.parts
    if parts[0] not in PARA_ROOTS:
        return True
    return any(p in SKIP_DIRS for p in parts) or parts[-1] in SKIP_FILES


def upsert_batch(points: list[dict], host: str, port: str, api_key: str | None) -> None:
    qdrant_req("PUT", f"/collections/{COLLECTION}/points", {"points": points}, host, port, api_key)


def delete_file_vectors(file_path: str, host: str, port: str, api_key: str | None) -> None:
    normalized = file_path.replace("\\", "/")
    qdrant_req(
        "POST",
        f"/collections/{COLLECTION}/points/delete",
        {"filter": {"must": [{"key": "file_path", "match": {"value": normalized}}]}},
        host, port, api_key,
    )
    print(f"  deleted vectors for: {normalized}")


# ── frontmatter ───────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    fm: dict = {}
    if not text.startswith("---"):
        return fm
    end = text.find("---", 3)
    if end == -1:
        return fm
    for line in text[3:end].splitlines():
        m = re.match(r"^(\w+):\s*(.+)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if v.startswith("[") and v.endswith("]"):
            fm[k] = [t.strip().strip("\"'") for t in v[1:-1].split(",") if t.strip()]
        else:
            fm[k] = v.strip("\"'")
    return fm


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    return text[end + 3:].lstrip("\n") if end != -1 else text


def infer_meta(path: Path, root: Path) -> tuple[str, str, str]:
    parts = path.relative_to(root).parts
    context = parts[0] if parts[0] in ("personal", "professional", "public") else ""
    project = parts[2] if len(parts) >= 3 and parts[1] == "projects" else ""
    para = parts[1] if len(parts) >= 2 and parts[1] in ("projects", "areas", "resources", "archive") else ""
    return context, project, para


# ── chunking ──────────────────────────────────────────────────────────────────

def split_sections(body: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(body))
    if not matches:
        return [("__preamble__", body)]
    sections: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        sections.append(("__preamble__", body[: matches[0].start()]))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections.append((m.group(1).strip(), body[m.end(): end].strip()))
    return sections


def chunk_section(heading: str, body: str) -> list[tuple[str, int]]:
    prefix = f"## {heading}\n\n" if heading != "__preamble__" else ""
    full = (prefix + body).strip()
    if len(full) <= MAX_CHARS:
        return [(full, 0)]
    chunks: list[tuple[str, int]] = []
    pos = 0
    idx = 0
    while pos < len(full):
        chunks.append((full[pos: pos + MAX_CHARS], idx))
        pos += MAX_CHARS - OVERLAP_CHARS
        idx += 1
    return chunks


# ── point ID ──────────────────────────────────────────────────────────────────

def make_point_id(file_path: str, heading: str, idx: int) -> str:
    raw = f"{file_path}:{heading}:{idx}"
    h = hashlib.sha1(raw.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="*", default=None, help="Specific files to embed (incremental)")
    parser.add_argument("--deleted", nargs="*", default=None, help="Files whose vectors should be removed")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    load_dotenv(root)

    ollama_host = os.environ.get("OLLAMA_HOST", "")
    ollama_port = os.environ.get("OLLAMA_PORT", "11434")
    ollama_key = os.environ.get("OLLAMA_API_KEY") or None
    qdrant_host = os.environ.get("QDRANT_HOST", "")
    qdrant_port = os.environ.get("QDRANT_PORT", "6333")
    qdrant_key = os.environ.get("QDRANT_API_KEY") or None

    if not ollama_host or not qdrant_host:
        print("RAG not configured (OLLAMA_HOST or QDRANT_HOST not set) — skipping embed.")
        return

    try:
        ensure_collection(qdrant_host, qdrant_port, qdrant_key)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    for f in (args.deleted or []):
        delete_file_vectors(f, qdrant_host, qdrant_port, qdrant_key)

    if args.files is not None:
        md_files: list[Path] = [root / f for f in args.files if f.endswith(".md")]
    else:
        md_files = sorted(root.rglob("*.md"))

    batch: list[dict] = []
    total_chunks = 0
    total_files = 0
    embed_failures = 0

    for md_file in md_files:
        rel = md_file.relative_to(root)
        if should_skip(rel):
            continue

        text = md_file.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        body = strip_frontmatter(text)
        ctx, project, para = infer_meta(md_file, root)

        context = fm.get("context", ctx)
        para_cat = fm.get("para", para)
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]

        file_path = str(rel).replace("\\", "/")
        file_chunks = 0

        for heading, section_body in split_sections(body):
            for chunk_text, idx in chunk_section(heading, section_body):
                if len(chunk_text.strip()) < MIN_CHARS:
                    continue
                try:
                    vec = ollama_embed(chunk_text, ollama_host, ollama_port, ollama_key)
                except Exception as e:
                    print(f"  WARN embed failed [{file_path} / {heading}]: {e}", file=sys.stderr)
                    embed_failures += 1
                    continue

                point_id = make_point_id(file_path, heading, idx)
                batch.append({
                    "id": point_id,
                    "vector": vec,
                    "payload": {
                        "file_path": file_path,
                        "heading": heading,
                        "para_category": para_cat,
                        "context": context,
                        "project": project,
                        "tags": tags,
                        "snippet": chunk_text[:300],
                    },
                })
                file_chunks += 1
                total_chunks += 1

                if len(batch) >= BATCH_SIZE:
                    upsert_batch(batch, qdrant_host, qdrant_port, qdrant_key)
                    batch.clear()
                    print(f"  flushed batch ({total_chunks} chunks total)", flush=True)

        if file_chunks:
            total_files += 1
            print(f"  {file_path} -> {file_chunks} chunk(s)")

    if batch:
        upsert_batch(batch, qdrant_host, qdrant_port, qdrant_key)

    print(f"\nDone. {total_files} files, {total_chunks} chunks upserted to '{COLLECTION}'.")

    if embed_failures > 0 and total_chunks == 0:
        print(f"Error: all {embed_failures} embed attempts failed — Ollama may be unreachable.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
