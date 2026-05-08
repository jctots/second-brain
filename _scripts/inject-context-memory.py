#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — injects project _memory.md on the first turn only.
import sys
import json
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

CONTEXTS = ["personal", "professional", "public"]


def get_first_user_message(transcript_path: str) -> str | None:
    path = Path(transcript_path)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if entry.get("type") == "user":
                msg = entry.get("message", {})
                if isinstance(msg, dict):
                    for block in msg.get("content", []):
                        if isinstance(block, dict) and block.get("type") == "text":
                            return block.get("text", "")
                elif isinstance(msg, str):
                    return msg
        except json.JSONDecodeError:
            continue
    return None


def find_projects_in_message(cwd: Path, message: str) -> list[Path]:
    message_lower = message.lower()
    found = []
    for context in CONTEXTS:
        projects_dir = cwd / context / "projects"
        if not projects_dir.exists():
            continue
        for project_dir in sorted(projects_dir.iterdir()):
            if not project_dir.is_dir() or project_dir.name.startswith("."):
                continue
            name_hyphen = project_dir.name.lower()
            name_space = name_hyphen.replace("-", " ")
            if name_hyphen in message_lower or name_space in message_lower:
                found.append(project_dir)
    return found


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


def summary_only(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
        for project_dir in find_projects_in_message(cwd, message):
            memory_md = project_dir / "_memory.md"
            if memory_md.exists():
                label = f"Project _memory.md auto-loaded for `{project_dir.name}` ({project_dir.parent.parent.name}/projects/):"
                output_parts.append(label + "\n\n" + summary_only(memory_md))

    if output_parts:
        print("\n\n---\n\n".join(output_parts))


if __name__ == "__main__":
    main()
