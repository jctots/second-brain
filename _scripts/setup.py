#!/usr/bin/env python3
"""
Second Brain — setup.
Installs pip dependencies, VS Code extensions, and configures optional services.
Called by setup.sh / setup.ps1 after Python is bootstrapped.

Usage:
    python _scripts/setup.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
STACK_YAML = VAULT_ROOT / "_infrastructure" / "stack.yaml"
REQUIREMENTS = Path(__file__).parent / "requirements.txt"
ENV_FILE = VAULT_ROOT / ".env"
CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"


# ── stack.yaml ─────────────────────────────────────────────────────────────────

def parse_vscode_extensions() -> list[str]:
    extensions: list[str] = []
    in_extensions = False
    for line in STACK_YAML.read_text(encoding="utf-8").splitlines():
        if "extensions:" in line:
            in_extensions = True
            continue
        if in_extensions:
            stripped = line.strip()
            if stripped.startswith("- "):
                extensions.append(stripped[2:].strip())
            elif stripped and not stripped.startswith("#"):
                in_extensions = False
    return extensions


# ── pip dependencies ───────────────────────────────────────────────────────────

def install_pip_deps() -> None:
    print("\n[1/3] Installing pip dependencies...")
    if not REQUIREMENTS.exists():
        print("  requirements.txt not found — skipping.")
        return
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "-r", str(REQUIREMENTS)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  Warning: pip returned errors:\n{result.stderr}")
    else:
        print("  ✓ Done.")


# ── VS Code extensions ─────────────────────────────────────────────────────────

def install_extensions() -> None:
    print("\n[2/3] Installing VS Code extensions...")
    extensions = parse_vscode_extensions()
    if not extensions:
        print("  No extensions found in stack.yaml — skipping.")
        return
    code_cmd = "code.cmd" if sys.platform == "win32" else "code"
    if subprocess.run([code_cmd, "--version"], capture_output=True).returncode != 0:
        print("  VS Code (code) not in PATH — skipping.")
        return
    for ext in extensions:
        print(f"  Installing: {ext}")
        subprocess.run([code_cmd, "--install-extension", ext, "--force"], capture_output=True)
    print("  ✓ Done.")


# ── git remotes ───────────────────────────────────────────────────────────────

def _git_remote_url(name: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(VAULT_ROOT), "remote", "get-url", name],
            capture_output=True, text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def configure_git_remotes() -> None:
    print("\n[3/5] Repository configuration")
    print()

    current_origin = _git_remote_url("origin")
    current_upstream = _git_remote_url("upstream")

    print(f"  origin   (your private git host): {current_origin or '(not set)'}")
    print(f"  upstream (public GitHub fork):     {current_upstream or '(not set)'}")
    print()
    print("  Press Enter to keep current values.")

    try:
        new_origin = input(f"  origin [{current_origin or 'e.g. https://gitea.example.com/you/second-brain.git'}]: ").strip()
        new_upstream = input(f"  upstream [{current_upstream or 'e.g. https://github.com/you/second-brain.git'}]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n  Skipped.")
        return

    if new_origin and new_origin != current_origin:
        subprocess.run(["git", "-C", str(VAULT_ROOT), "remote", "set-url", "origin", new_origin], check=True)
        print(f"  ✓ origin set to {new_origin}")
    elif new_origin:
        print("  origin unchanged.")

    if new_upstream:
        if current_upstream:
            subprocess.run(["git", "-C", str(VAULT_ROOT), "remote", "set-url", "upstream", new_upstream], check=True)
            print(f"  ✓ upstream set to {new_upstream}")
        else:
            subprocess.run(["git", "-C", str(VAULT_ROOT), "remote", "add", "upstream", new_upstream], check=True)
            print(f"  ✓ upstream added: {new_upstream}")
    else:
        if current_upstream:
            print("  upstream unchanged.")
        else:
            print("  upstream not configured (Tier 1 default — skip if using GitHub as origin).")


# ── optional services ──────────────────────────────────────────────────────────

SERVICES: list[dict] = [
    {
        "key": "rag",
        "name": "RAG (Ollama + Qdrant)",
        "description": "Passive note surfacing, /search command",
        "tier": "Tier 2/3",
        "config_type": "env",
        "detect_key": "OLLAMA_HOST",
        "pip_package": None,
        "prompts": [
            ("OLLAMA_HOST", "Ollama hostname or IP", ""),
            ("OLLAMA_PORT", "Ollama port", "11434"),
            ("QDRANT_HOST", "Qdrant hostname or IP", ""),
            ("QDRANT_PORT", "Qdrant port", "6333"),
        ],
    },
    {
        "key": "ntfy",
        "name": "ntfy",
        "description": "Push notifications — session events, health check, CI failures",
        "tier": "Any",
        "config_type": "env",
        "detect_key": "NTFY_URL",
        "pip_package": None,
        "prompts": [
            ("NTFY_URL", "ntfy server URL (e.g. https://your-ntfy-host)", ""),
            ("NTFY_TOPIC", "ntfy topic (used for all notifications)", "second-brain"),
            ("NTFY_ON_EVENTS", "Notify on unprocessed session events (true/false)", "true"),
        ],
        "tips": {
            "NTFY_URL": "CI failure notifications use Gitea secrets (NTFY_URL, NTFY_TOPIC) — set those separately in Gitea → Settings → Secrets.",
        },
    },
    {
        "key": "vikunja",
        "name": "Vikunja",
        "description": "Task management — /remember creates and syncs tasks",
        "tier": "Any",
        "config_type": "env",
        "detect_key": "VIKUNJA_URL",
        "pip_package": "vikunja-mcp",
        "write_mcp_json": True,
        "prompts": [
            ("VIKUNJA_URL", "Vikunja base URL (e.g. https://your-vikunja-host)", ""),
            ("VIKUNJA_TOKEN", "Vikunja API token", ""),
        ],
        "tips": {
            "VIKUNJA_TOKEN": "In Vikunja: Settings → API Tokens → create with unlimited scope.",
        },
    },
    {
        "key": "litellm",
        "name": "LiteLLM gateway",
        "description": "Route Claude Code to local Ollama/vLLM",
        "tier": "Tier 2/3",
        "config_type": "manual",
        "detect_key": "ANTHROPIC_BASE_URL",
        "pip_package": None,
        "prompts": [],
    },
]


def read_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    env: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def write_env(updates: dict[str, str]) -> None:
    lines: list[str] = []
    updated: set[str] = set()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k, _, _ = stripped.partition("=")
                k = k.strip()
                if k in updates:
                    lines.append(f"{k}={updates[k]}")
                    updated.add(k)
                    continue
            lines.append(line)
    for k, v in updates.items():
        if k not in updated:
            lines.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_claude_settings() -> dict:
    if not CLAUDE_SETTINGS.exists():
        return {}
    try:
        return json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_claude_settings(settings: dict) -> None:
    CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def _is_secret(key: str) -> bool:
    return any(w in key.upper() for w in ("TOKEN", "SECRET", "KEY", "PASSWORD"))


def is_configured(service: dict, env: dict, settings: dict) -> bool:
    if service["config_type"] == "env":
        return bool(env.get(service["detect_key"], "").strip())
    if service["config_type"] == "mcp":
        return service["detect_key"] in settings.get("mcpServers", {})
    if service["config_type"] == "manual":
        return bool(os.environ.get(service["detect_key"], "").strip())
    return False


def prompt_value(key: str, label: str, default: str, current: str) -> str:
    if current:
        hint = "[current: ********]" if _is_secret(key) else f"[current: {current}]"
        prompt = f"  {label} {hint}: "
    elif default:
        prompt = f"  {label} [default: {default}]: "
    else:
        prompt = f"  {label}: "
    value = input(prompt).strip()
    return value or current or default


def configure_service(service: dict, env: dict, settings: dict) -> tuple[dict, dict]:
    print(f"\n  {service['name']}")

    if service["config_type"] == "manual":
        print("  LiteLLM requires shell environment variables — cannot be auto-configured.")
        print("  Add to your shell profile (.bashrc / .zshrc / PowerShell profile):\n")
        print("    ANTHROPIC_API_KEY=<your-anthropic-api-key>")
        print("    ANTHROPIC_BASE_URL=http://<litellm-host>:4000")
        print("    ANTHROPIC_AUTH_TOKEN=<your-litellm-key>")
        print("\n  See architecture.md § LiteLLM gateway interface for details.")
        return env, settings

    if service["pip_package"]:
        print(f"  Installing {service['pip_package']}...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", service["pip_package"]],
            check=True,
        )
        print(f"  ✓ {service['pip_package']} installed.")

    current_mcp_env: dict[str, str] = {}
    if service["config_type"] == "mcp":
        current_mcp_env = (
            settings.get("mcpServers", {})
            .get(service["detect_key"], {})
            .get("env", {})
        )

    env_updates: dict[str, str] = {}
    mcp_env: dict[str, str] = {}

    tips = service.get("tips", {})
    for key, label, default in service["prompts"]:
        if key in tips:
            print(f"  ℹ  {tips[key]}")
        current = env.get(key, "") if service["config_type"] == "env" else current_mcp_env.get(key, "")
        value = prompt_value(key, label, default, current)
        if service["config_type"] == "env":
            env_updates[key] = value
        else:
            mcp_env[key] = value

    if service["config_type"] == "env":
        write_env(env_updates)
        env.update(env_updates)
        print("  ✓ Written to .env")

        if service.get("write_mcp_json"):
            mcp_json_path = VAULT_ROOT / ".mcp.json"
            mcp_config = {
                "mcpServers": {
                    service["key"]: {
                        "type": "stdio",
                        "command": service["key"] + "-mcp",
                        "env": {k: env_updates[k] for k in env_updates},
                    }
                }
            }
            mcp_json_path.write_text(json.dumps(mcp_config, indent=2) + "\n", encoding="utf-8")
            print(f"  ✓ Written to .mcp.json")
            print("  ↺ Restart Claude Code for MCP changes to take effect.")

    elif service["config_type"] == "mcp":
        if "mcpServers" not in settings:
            settings["mcpServers"] = {}
        settings["mcpServers"][service["detect_key"]] = {
            "command": "vikunja-mcp",
            "env": mcp_env,
        }
        write_claude_settings(settings)
        print(f"  ✓ Written to {CLAUDE_SETTINGS}")
        print("  ↺ Restart Claude Code for MCP changes to take effect.")

    return env, settings


def configure_optional_services() -> None:
    print("\n[2/2] Optional services")

    env = read_env()
    settings = read_claude_settings()

    print("\n  Current status:")
    for i, svc in enumerate(SERVICES, 1):
        status = "✓" if is_configured(svc, env, settings) else "✗"
        print(f"  {i}. [{status}] {svc['name']} — {svc['description']} ({svc['tier']})")

    print()
    print("  Enter numbers (e.g. 1 3), 'all' for unconfigured, 'r' to reconfigure, Enter to skip.")

    try:
        choice = input("\n  > ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n  Skipped.")
        return

    if not choice:
        print("  Skipped.")
        return

    to_configure: list[dict] = []

    if choice == "all":
        to_configure = [s for s in SERVICES if not is_configured(s, env, settings)]
        if not to_configure:
            print("  All services already configured.")
            return
    elif choice == "r":
        print("\n  Which service to reconfigure?")
        for i, svc in enumerate(SERVICES, 1):
            print(f"  {i}. {svc['name']}")
        try:
            to_configure = [SERVICES[int(input("  > ").strip()) - 1]]
        except (ValueError, IndexError, KeyboardInterrupt, EOFError):
            print("  Invalid selection.")
            return
    else:
        for part in choice.split():
            try:
                to_configure.append(SERVICES[int(part) - 1])
            except (ValueError, IndexError):
                print(f"  Skipping invalid: {part}")

    if not to_configure:
        print("  Nothing to configure.")
        return

    for svc in to_configure:
        try:
            env, settings = configure_service(svc, env, settings)
        except (KeyboardInterrupt, EOFError):
            print("\n  Interrupted.")
            break


# ── change configuration ───────────────────────────────────────────────────────

def _cfg_pdf_sidecars() -> None:
    print("\n  PDF sidecars are enabled via a Gitea Actions variable — not in .env.")
    print()
    print("  To enable:")
    print("    Gitea → your repo → Settings → Variables → Add variable")
    print("    Name:  PDF_SIDECARS_ENABLED")
    print("    Value: true")
    print()
    print("  To disable: delete or set the variable to any other value.")
    print("  Dependencies (tesseract, pdfplumber) are installed automatically in CI when enabled.")


def _cfg_hook_budget() -> None:
    env = read_env()
    print()
    print(f"  Current HOOK_BUDGET_HARD    : {env.get('HOOK_BUDGET_HARD', '10000 (default)')}")
    print(f"  Current HOOK_BUDGET_WARN_PCT: {env.get('HOOK_BUDGET_WARN_PCT', '80 (default)')}")
    print()
    print("  To change: edit .env at vault root and set:")
    print("    HOOK_BUDGET_HARD=10000     # hard char limit per file — CI fails above this")
    print("    HOOK_BUDGET_WARN_PCT=80    # warn threshold as % of hard limit")
    print()
    print("  These affect: test_hook_budget.py (CI), generate-dashboard.py (budget section),")
    print("  and check-health.py (startup health check).")


def _cfg_ntfy_toggles() -> None:
    env = read_env()
    current_events = env.get("NTFY_ON_EVENTS", "true")

    print()
    print(f"  NTFY_ON_EVENTS (session events): {current_events}")
    print()
    print("  Note: CI failure notifications are controlled via Gitea secrets (NTFY_URL, NTFY_TOPIC),")
    print("  not .env — toggle them by adding or removing those secrets in Gitea.")
    print("  Service health failures are shown in-conversation, not via ntfy.")
    print()

    try:
        new_events = input(f"  NTFY_ON_EVENTS [current: {current_events}] (true/false, Enter to keep): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n  Skipped.")
        return

    updates: dict[str, str] = {}
    if new_events in ("true", "false"):
        updates["NTFY_ON_EVENTS"] = new_events

    if updates:
        write_env(updates)
        for k, v in updates.items():
            print(f"  ✓ {k}={v} written to .env")
    else:
        print("  No changes.")


def configure_settings() -> None:
    print("\n  Change configuration")
    print()
    print("  1. PDF sidecars — how to enable/disable in Gitea")
    print("  2. Hook budget  — how to adjust limits in .env")
    print("  3. ntfy events  — toggle session and health notifications")
    print("  4. Git remotes  — set origin and upstream URLs")
    print()

    try:
        choice = input("  > ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n  Skipped.")
        return

    if choice == "1":
        _cfg_pdf_sidecars()
    elif choice == "2":
        _cfg_hook_budget()
    elif choice == "3":
        _cfg_ntfy_toggles()
    elif choice == "4":
        configure_git_remotes()
    else:
        print("  Invalid selection.")


# ── entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    print("Second Brain — Setup")
    print("=" * 40)
    print()
    print("  1. Full setup — pip deps, VS Code extensions, optional services")
    print("  2. Optional services only")
    print("  3. Change configuration")
    print()
    try:
        mode = input("  > ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        return

    if mode == "2":
        configure_optional_services()
    elif mode == "3":
        configure_settings()
    else:
        install_pip_deps()
        install_extensions()
        configure_optional_services()

    print("\nSetup complete.")


if __name__ == "__main__":
    main()
