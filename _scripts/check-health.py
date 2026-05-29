#!/usr/bin/env python3
# Startup health check — run on VS Code folder open via .vscode/tasks.json.
# Checks configured optional services (Ollama, Qdrant, Vikunja) and hook injection
# budget (via test_hook_budget.py). Sends ntfy notifications for any failures.
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent


def load_dotenv() -> None:
    env_file = VAULT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def ntfy(base_url: str, topic: str, title: str, message: str) -> None:
    try:
        url = f"{base_url.rstrip('/')}/{topic}"
        req = urllib.request.Request(url, data=message.encode("utf-8"), method="POST")
        req.add_header("Title", title)
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def check(label: str, url: str, headers: dict | None = None, timeout: int = 5) -> bool:
    try:
        req = urllib.request.Request(url)
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except (urllib.error.URLError, OSError):
        return False


def run_budget_check() -> tuple[bool, str]:
    test_script = VAULT_ROOT / "_tests" / "test_hook_budget.py"
    if not test_script.exists():
        return True, ""
    try:
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True, text=True, timeout=30,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except Exception:
        return True, ""


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

    load_dotenv()

    ntfy_url = os.environ.get("NTFY_URL", "")
    ntfy_topic = os.environ.get("NTFY_TOPIC", "second-brain")
    ntfy_on_health = os.environ.get("NTFY_ON_HEALTH", "true").lower() != "false"
    timeout = int(os.environ.get("RAG_TIMEOUT", "5"))

    failures: list[str] = []

    # RAG — Ollama
    ollama_host = os.environ.get("OLLAMA_HOST", "")
    ollama_port = os.environ.get("OLLAMA_PORT", "11434")
    if ollama_host:
        if not check("Ollama", f"http://{ollama_host}:{ollama_port}/api/tags", timeout=timeout):
            failures.append(f"Ollama unreachable ({ollama_host}:{ollama_port})")

    # RAG — Qdrant
    qdrant_host = os.environ.get("QDRANT_HOST", "")
    qdrant_port = os.environ.get("QDRANT_PORT", "6333")
    if qdrant_host:
        if not check("Qdrant", f"http://{qdrant_host}:{qdrant_port}/readyz", timeout=timeout):
            failures.append(f"Qdrant unreachable ({qdrant_host}:{qdrant_port})")

    # Vikunja
    vikunja_url = os.environ.get("VIKUNJA_URL", "")
    vikunja_token = os.environ.get("VIKUNJA_TOKEN", "")
    if vikunja_url and vikunja_token:
        if not check("Vikunja", f"{vikunja_url}/api/v1/user",
                     headers={"Authorization": f"Bearer {vikunja_token}"}, timeout=timeout):
            failures.append(f"Vikunja unreachable ({vikunja_url})")

    if failures:
        summary = ", ".join(failures)
        print(f"⚠️ Service check: {summary}")
        if ntfy_url and ntfy_on_health:
            ntfy(ntfy_url, ntfy_topic, "🔴 Second Brain: services unavailable", summary)
    else:
        configured = [s for s in ["Ollama" if ollama_host else "",
                                   "Qdrant" if qdrant_host else "",
                                   "Vikunja" if vikunja_url else ""] if s]
        if configured:
            print(f"✓ Services reachable: {', '.join(configured)}")

    budget_ok, budget_output = run_budget_check()
    warn_fail_lines = [l for l in budget_output.splitlines() if l.startswith(("WARN", "FAIL"))]
    if warn_fail_lines:
        msg = "\n".join(warn_fail_lines)
        print(f"⚠️ Budget:\n{msg}")
        if ntfy_url and ntfy_on_health:
            title = "⛔ Second Brain: budget hard limit exceeded" if not budget_ok else "⚠️ Second Brain: budget approaching limit"
            ntfy(ntfy_url, ntfy_topic, title, msg + " — run /maintain option 4")


if __name__ == "__main__":
    main()
