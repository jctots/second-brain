#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — service reachability check on first turn only.
# Checks configured optional services (Ollama, Qdrant, Vikunja, Gitea, ntfy).
# Silent on success; prints failures to stdout (shown in conversation context).
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

VAULT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import is_first_turn, load_dotenv  # noqa: E402


def check(url: str, headers: dict | None = None, timeout: int = 5) -> bool:
    try:
        req = urllib.request.Request(url)
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except (urllib.error.URLError, OSError):
        return False


def main() -> None:
    import os

    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    try:
        hook_data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    transcript_path = hook_data.get("transcript_path")
    if transcript_path and not is_first_turn(transcript_path):
        sys.exit(0)

    load_dotenv(VAULT_ROOT)

    timeout = int(os.environ.get("RAG_TIMEOUT", "5"))
    failures: list[str] = []

    # Ollama
    ollama_host = os.environ.get("OLLAMA_HOST", "")
    ollama_port = os.environ.get("OLLAMA_PORT", "11434")
    if ollama_host:
        if not check(f"http://{ollama_host}:{ollama_port}/api/tags", timeout=timeout):
            failures.append(f"Ollama unreachable ({ollama_host}:{ollama_port})")

    # Qdrant
    qdrant_host = os.environ.get("QDRANT_HOST", "")
    qdrant_port = os.environ.get("QDRANT_PORT", "6333")
    if qdrant_host:
        if not check(f"http://{qdrant_host}:{qdrant_port}/readyz", timeout=timeout):
            failures.append(f"Qdrant unreachable ({qdrant_host}:{qdrant_port})")

    # Vikunja
    vikunja_url = os.environ.get("VIKUNJA_URL", "")
    vikunja_token = os.environ.get("VIKUNJA_TOKEN", "")
    if vikunja_url and vikunja_token:
        if not check(f"{vikunja_url}/api/v1/user",
                     headers={"Authorization": f"Bearer {vikunja_token}"}, timeout=timeout):
            failures.append(f"Vikunja unreachable ({vikunja_url})")

    # Gitea
    gitea_url = os.environ.get("GITEA_URL", "")
    gitea_token = os.environ.get("GITEA_TOKEN", "")
    if gitea_url and gitea_token:
        if not check(f"{gitea_url}/api/v1/user",
                     headers={"Authorization": f"Bearer {gitea_token}"}, timeout=timeout):
            failures.append(f"Gitea unreachable ({gitea_url})")

    # ntfy
    ntfy_url = os.environ.get("NTFY_URL", "")
    if ntfy_url:
        if not check(ntfy_url.rstrip("/"), timeout=timeout):
            failures.append(f"ntfy unreachable ({ntfy_url})")

    if failures:
        print(f"⚠️ Service check: {', '.join(failures)}")


if __name__ == "__main__":
    main()
