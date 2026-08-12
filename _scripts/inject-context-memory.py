#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — injects project _memory.md on the first turn only.
import sys
import json
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

sys.path.insert(0, str(Path(__file__).parent))
from _hook_utils import (  # noqa: E402
    is_first_turn,
    get_first_user_message,
    get_ide_opened_file,
    find_project_from_file,
    strip_ide_selection,
    find_projects_in_message,
    emit_capped,
    hook_budget,
)


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

    output_parts = []

    if transcript_path:
        message = hook_data.get("prompt", "") or get_first_user_message(transcript_path) or ""
        projects = find_projects_in_message(cwd, strip_ide_selection(message))
        if not projects:
            ide_file = get_ide_opened_file(transcript_path)
            if ide_file:
                projects = find_project_from_file(cwd, ide_file)
        for project_dir in projects:
            memory_md = project_dir / "_memory.md"
            if memory_md.exists():
                rel = f"{project_dir.parent.parent.name}/projects/{project_dir.name}"
                label = f"Project _memory.md auto-loaded for `{project_dir.name}` ({project_dir.parent.parent.name}/projects/):"
                full = label + "\n\n" + memory_md.read_text(encoding="utf-8")
                pointer = f"Project _memory.md for `{project_dir.name}` did not fit the hook budget — read `{rel}/_memory.md` before working on it."
                output_parts.append((full, pointer))

    if output_parts:
        print(emit_capped(output_parts, hook_budget(cwd)))


if __name__ == "__main__":
    main()
