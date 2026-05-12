#!/usr/bin/env python3
# Scans _conversations/ for files with unprocessed events and writes _inbox/pending-events.md.
# Run from repo root: python _scripts/generate-pending-events.py
import json
import re
from datetime import datetime
from pathlib import Path

# Maps event type → the processed token that clears it
EVENT_TO_PROCESSED = {
    "memory": "memory",
    "profile": "profile",
    "distill": "distill",
    "task": "task",
}


def parse_frontmatter(path):
    fm = {"events": [], "processed": []}
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    in_fm = False
    started = False
    for line in lines:
        stripped = line.strip()
        if not started and stripped == "---":
            in_fm = True
            started = True
            continue
        if in_fm and stripped == "---":
            break
        if not in_fm:
            break
        m = re.match(r"^events:\s*(\[.*\])\s*$", line)
        if m:
            try:
                fm["events"] = json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
            continue
        m = re.match(r"^processed:\s*(\[.*\])\s*$", line)
        if m:
            try:
                fm["processed"] = json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
    return fm


def main():
    root = Path(__file__).parent.parent
    conv_dir = root / "_conversations"
    output_path = root / "_conversations" / "pending-events.md"

    files = [f for f in conv_dir.rglob("*.md") if f.name != "index.md"]

    pending_entries = []
    for f in files:
        if len(f.stem) < 10:
            continue
        fm = parse_frontmatter(f)
        events = fm["events"]
        processed = fm["processed"]
        if not events:
            continue
        pending = [e for e in events if EVENT_TO_PROCESSED.get(e) not in processed]
        if not pending:
            continue
        rel = f.relative_to(root).with_suffix("")
        wikilink = "[[" + rel.as_posix() + "]]"
        date = f.stem[:10]
        pending_entries.append({"date": date, "link": wikilink, "pending": pending})

    pending_entries.sort(key=lambda e: e["date"], reverse=True)

    updated = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    lines = [
        "<!-- AUTO-GENERATED - do not edit manually. Run _scripts/generate-pending-events.py to refresh. -->",
        "",
        "# Pending Events",
        "",
    ]

    if pending_entries:
        lines.append(f"_{len(pending_entries)} conversation(s) with unprocessed events as of {updated}. Run `/maintain` option 2 to process._")
        lines.append("")
        for e in pending_entries:
            pending_str = ", ".join(e["pending"])
            lines.append(f"- {e['link']} — pending: {pending_str}")
    else:
        lines.append(f"_No pending events as of {updated}._")

    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Pending events: {len(pending_entries)} conversation(s) flagged.")


if __name__ == "__main__":
    main()
