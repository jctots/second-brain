#!/usr/bin/env python3
# Query the vault via semantic search.
# Usage: python _scripts/rag-search.py "your query"
# Env vars (or .env at repo root): OLLAMA_HOST, OLLAMA_PORT, OLLAMA_API_KEY,
#                                   QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

COLLECTION = "second_brain"
EMBED_MODEL = "embeddinggemma:latest"
TOP_K = 5


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
    payload = json.dumps({"vector": vector, "limit": TOP_K, "with_payload": True}).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    if api_key:
        req.add_header("api-key", api_key)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["result"]


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python _scripts/rag-search.py \"your query\"", file=sys.stderr)
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    root = Path(__file__).parent.parent
    load_dotenv(root)

    ollama_host = os.environ.get("OLLAMA_HOST", "192.168.30.33")
    ollama_port = os.environ.get("OLLAMA_PORT", "11434")
    ollama_key = os.environ.get("OLLAMA_API_KEY") or None
    qdrant_host = os.environ.get("QDRANT_HOST", "192.168.30.33")
    qdrant_port = os.environ.get("QDRANT_PORT", "6333")
    qdrant_key = os.environ.get("QDRANT_API_KEY") or None

    vec = ollama_embed(query, ollama_host, ollama_port, ollama_key)
    results = qdrant_search(vec, qdrant_host, qdrant_port, qdrant_key)

    if not results:
        print("No results.")
        return

    print(f"Query: {query}\n")
    for i, hit in enumerate(results, 1):
        p = hit["payload"]
        score = hit["score"]
        file_path = p.get("file_path", "")
        heading = p.get("heading", "")
        snippet = p.get("snippet", "").replace("\n", " ").strip()
        heading_str = f" § {heading}" if heading and heading != "__preamble__" else ""
        print(f"{i}  {score:.2f} | {file_path}{heading_str}")
        print(f"   {snippet[:200]}".encode("ascii", errors="replace").decode("ascii"))
        print()


if __name__ == "__main__":
    main()
