#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — injects _self/rules.md on the first turn only.
import sys
import json
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)


def is_first_turn(transcript_path: str) -> bool:
    path = Path(transcript_path)
    if not path.exists():
        return True
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if entry.get("type") == "assistant":
                return False
        except json.JSONDecodeError:
            continue
    return True


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    try:
        hook_data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    transcript_path = hook_data.get("transcript_path")
    cwd = Path(hook_data.get("cwd", "."))

    if transcript_path and not is_first_turn(transcript_path):
        sys.exit(0)

    rules_path = cwd / "_self/rules.md"
    if rules_path.exists():
        content = rules_path.read_text(encoding="utf-8")
        print(f"The following is JC's Claude rules, loaded automatically at session start:\n\n{content}")


if __name__ == "__main__":
    main()
