#!/usr/bin/env python3
# Claude Code UserPromptSubmit hook — injects a lightweight registry of all active projects.
# First turn only. Scans {personal,professional,public}/projects/ and extracts snapshot lines.
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

CONTEXTS = ["personal", "professional", "public"]


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


def extract_snapshot(memory_path: Path) -> str | None:
    try:
        lines = memory_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    in_snapshot = False
    for line in lines:
        if line.strip() == "## Snapshot":
            in_snapshot = True
            continue
        if in_snapshot:
            if line.startswith("## "):
                break
            text = line.strip()
            if text:
                return text
    return None


def collect_projects(cwd: Path) -> list[tuple[str, str | None]]:
    """Return (relative_path, snapshot_or_None) for all active projects, sorted by context then name."""
    results = []
    for context in CONTEXTS:
        projects_dir = cwd / context / "projects"
        if not projects_dir.exists():
            continue
        for project_dir in sorted(projects_dir.iterdir()):
            if not project_dir.is_dir() or project_dir.name.startswith("."):
                continue
            memory_md = project_dir / "_memory.md"
            snapshot = extract_snapshot(memory_md) if memory_md.exists() else None
            rel = f"{context}/projects/{project_dir.name}"
            results.append((rel, snapshot))
    return results


def main() -> None:
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

    projects = collect_projects(cwd)
    if not projects:
        sys.exit(0)

    lines = ["## Active Projects"]
    for rel_path, snapshot in projects:
        if snapshot:
            lines.append(f"- {rel_path} — {snapshot}")
        else:
            lines.append(f"- {rel_path}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
