#!/usr/bin/env python3
"""PreToolUse:Read|Grep|Bash guard blocking access to decrypted secrets files.

Written after a decrypted .env was read and diffed during a session,
printing its secrets into the transcript. A CLAUDE.md instruction not to
read .env files is not enough on its own — an agent that has already
decided the file is relevant will reach for it. This hook makes the access
structurally impossible instead of merely discouraged.

Scope: any file whose basename is exactly ".env" (not ".env.example", which
never matches — the check is an exact-name match, not a prefix match), in
any repo this agent's tools can reach. Covers three ways this agent could
have exposed the file: Read (direct), Grep (path/glob targeting it
explicitly), and Bash (cat/diff/git diff/grep/python -c/etc — too many
command shapes for a single permission-string pattern, hence a hook that
scans the command text instead).

Two outcomes:

    exit 2   DENY  — stderr to the agent, no ask/override path
    exit 0   allow — falls through to the normal permission flow

Fail-closed: if this hook raises, it denies. An exception here must never
read as "allowed".
"""
import json
import os
import re
import sys

# Matches a literal ".env" path component. Negative lookahead excludes
# ".env.example" (and any other ".env.*" suffix) without needing a
# separate allowlist — only the bare file is a secrets file.
ENV_FILE_RE = re.compile(r"(?:^|[/\\])\.env(?!\.\w)(?:\b|$)")


def deny(reason, detail):
    print(f"DENIED (env-guard): {reason}", file=sys.stderr)
    print(f"  {detail}", file=sys.stderr)
    print(
        "\n.env files are gated structurally, not by instruction — see"
        "\n.claude/hooks/env-guard.py. If you genuinely need a value from a"
        "\n.env file, ask the user to paste it or run the command themselves.",
        file=sys.stderr,
    )
    sys.exit(2)


def check_path(path: str, tool_name: str):
    if not path:
        return
    basename = os.path.basename(path.rstrip("/\\"))
    if basename == ".env":
        deny(f"{tool_name} targets a .env file", f"path: {path}")


def check_bash(cmd: str):
    if ENV_FILE_RE.search(cmd):
        deny("command references a .env file", f"command: {cmd}")


def main():
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name == "Read":
        check_path(tool_input.get("file_path", ""), tool_name)
    elif tool_name == "Grep":
        check_path(tool_input.get("path", ""), tool_name)
        check_path(tool_input.get("glob", ""), tool_name)
    elif tool_name == "Bash":
        cmd = tool_input.get("command", "")
        if cmd.strip():
            check_bash(cmd)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — deliberate catch-all, fail closed
        print(f"DENIED: env-guard failed to evaluate the call: {exc}", file=sys.stderr)
        print("  Fix the guard before continuing. Do not work around it.", file=sys.stderr)
        sys.exit(2)
