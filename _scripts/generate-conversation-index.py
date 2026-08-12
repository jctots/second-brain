#!/usr/bin/env python3
# Regenerates _conversations/index.md from frontmatter of all conversation files.
# Run from repo root: python _scripts/generate-conversation-index.py
import re
from pathlib import Path
from collections import defaultdict


def parse_frontmatter(path):
    fm = {"updated": "", "title": "", "projects": []}
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
        m = re.match(r"^updated:\s*(.+)$", line)
        if m:
            fm["updated"] = m.group(1).strip()
            continue
        m = re.match(r'^title:\s*"?(.+?)"?\s*$', line)
        if m:
            fm["title"] = m.group(1).strip()
            continue
        m = re.match(r"^projects:\s*\[(.+)\]$", line)
        if m:
            def clean(p):
                p = p.strip().strip('"')
                return p[2:-2] if p.startswith("[[") and p.endswith("]]") else p
            fm["projects"] = [clean(p) for p in m.group(1).split(",") if clean(p)]
    return fm


def main():
    root = Path(__file__).parent.parent
    conv_dir = root / "_conversations"
    index_path = conv_dir / "index.md"

    files = [f for f in conv_dir.rglob("*.md") if f.name not in ("index.md", "pending-events.md")]

    entries = []
    for f in files:
        fm = parse_frontmatter(f)
        if len(f.stem) < 10:
            continue
        date = f.stem[:10]
        entries.append({
            "stem": f.stem,
            "date": date,
            "updated": fm["updated"],
            "title": fm["title"] if fm["title"] else f.stem,
            "projects": fm["projects"],
        })

    entries.sort(key=lambda e: e["updated"] or e["date"], reverse=True)

    by_month = defaultdict(list)
    for e in entries:
        by_month[e["date"][:7]].append(e)

    lines = [
        "<!-- AUTO-GENERATED - do not edit manually. Run _scripts/generate-conversation-index.py to refresh. -->",
        "",
        "# 💬 Conversations",
        "",
        "[[dashboard|⬅️ Dashboard]]",
        "",
    ]

    for month in sorted(by_month.keys(), reverse=True):
        lines.append(f"## 📅 {month}")
        lines.append("")
        lines.append("| Date | Projects | Conversation |")
        lines.append("|------|----------|--------------|")
        for e in by_month[month]:
            projects_str = ", ".join(
                f"[[{p}/index\\|{p}]]" for p in e["projects"]
            ) if e["projects"] else ""
            conv_link = f"[[{e['stem']}]]"
            lines.append(f"| {e['date']} | {projects_str} | {conv_link} |")
        lines.append("")

    with open(index_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"Index updated: {len(entries)} conversations indexed.")


if __name__ == "__main__":
    main()
