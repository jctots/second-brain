#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — injects _self/corrections.md on the first turn only.
import sys
import json
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import is_first_turn, hook_budget  # noqa: E402


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

    rules_path = cwd / "_self/corrections.md"
    if rules_path.exists():
        content = rules_path.read_text(encoding="utf-8")
        header = "The following are your corrections, loaded automatically at session start:\n\n"
        if len(header) + len(content) > hook_budget(cwd):
            print("`_self/corrections.md` exceeds the hook budget and was not injected — read it now, then run /maintain option 5 to trim it.")
        else:
            print(header + content)


if __name__ == "__main__":
    main()
