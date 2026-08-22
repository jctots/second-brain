#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — warns when the session's current
# context size crosses a threshold, so a long session gets flagged before
# PreCompact fires (by then most of the window is already spent, and
# compaction itself costs an extra LLM call on top of that).
#
# Looks at the LAST assistant turn's usage block only: input_tokens +
# cache_read_input_tokens + cache_creation_input_tokens approximates the
# context currently loaded. Summing usage across every turn is wrong —
# cache_read_input_tokens re-counts the same reused context on every turn,
# so a naive sum overstates real spend by roughly an order of magnitude on
# a long session.
#
# Two-tier: a soft warning at SESSION_TOKEN_WARN_THRESHOLD (default 100000,
# 50% of the 200k window) and a critical one at
# SESSION_TOKEN_CRITICAL_THRESHOLD (default 150000, 75%). Only the
# higher-tier message prints once both are crossed. Silent below both, and
# silent (not an error) on missing/unparseable transcript data.
#
# Output format depends on the harness surface, verified live 2026-08-20:
# CLAUDE_CODE_ENTRYPOINT=claude-vscode (the VS Code extension) renders
# {"systemMessage": ...} JSON as NOTHING — silently dropped, confirmed by
# running a 375k-token session with zero warning ever appearing. Plain
# print() is what actually renders there (as a "UserPromptSubmit hook
# success: ..." wrapper — ugly, but visible). A CLI/terminal session (no
# claude-vscode entrypoint) renders systemMessage cleanly instead, which
# is worth using when available since it drops the wrapper text.
import json
import os
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)


def context_size(transcript_path: str) -> int:
    path = Path(transcript_path)
    if not path.exists():
        return 0
    last_usage = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") == "assistant":
            usage = entry.get("message", {}).get("usage")
            if usage:
                last_usage = usage
    if last_usage is None:
        return 0
    return (
        last_usage.get("input_tokens", 0)
        + last_usage.get("cache_read_input_tokens", 0)
        + last_usage.get("cache_creation_input_tokens", 0)
    )


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    try:
        hook_data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    transcript_path = hook_data.get("transcript_path")
    if not transcript_path:
        sys.exit(0)

    size = context_size(transcript_path)

    warn_threshold = int(os.environ.get("SESSION_TOKEN_WARN_THRESHOLD", "100000"))
    critical_threshold = int(os.environ.get("SESSION_TOKEN_CRITICAL_THRESHOLD", "150000"))

    if size >= critical_threshold:
        message = f"Session context is at ~{size} tokens (critical threshold {critical_threshold}) — wrap up or start fresh now."
    elif size >= warn_threshold:
        message = f"Session context is at ~{size} tokens (threshold {warn_threshold}) — consider wrapping up or starting fresh soon."
    else:
        return

    if os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "claude-vscode":
        print(message)
    else:
        print(json.dumps({"systemMessage": message}))


if __name__ == "__main__":
    main()
