#!/usr/bin/env python3
# Generates "## files", "## relevant conversations", and "## quick status" sections in all project index.md files.
# Run from repo root: python _scripts/generate-project-indices.py
import re
from pathlib import Path


def parse_quick_status(memory_path):
    if not memory_path.exists():
        return None, []
    lines = memory_path.read_text(encoding="utf-8").splitlines()
    in_section = False
    status = None
    next_items = []
    in_next = False
    for line in lines:
        if re.match(r"^## Quick status\s*$", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section and re.match(r"^## ", line):
            break
        if not in_section:
            continue
        m = re.match(r"^status:\s*(.+)$", line)
        if m:
            status = m.group(1).strip()
            in_next = False
            continue
        if re.match(r"^next:\s*$", line):
            in_next = True
            continue
        if in_next and line.startswith("- "):
            next_items.append(line[2:].strip())
    return status, next_items


def set_section(lines, heading, new_lines):
    escaped = re.escape(heading)
    sec_start = -1
    sec_end = len(lines)
    for i, line in enumerate(lines):
        if re.match(rf"^## {escaped}\s*$", line):
            sec_start = i
            for j in range(i + 1, len(lines)):
                if re.match(r"^## ", lines[j]):
                    sec_end = j
                    break
            break

    section = [f"## {heading}", ""] + list(new_lines)
    if sec_start >= 0:
        before = lines[:sec_start]
        after = ([""] + lines[sec_end:]) if sec_end < len(lines) else []
        return before + section + after
    else:
        while lines and not lines[-1].strip():
            lines = lines[:-1]
        return lines + [""] + section



def parse_conv_frontmatter(path):
    fm = {"updated": "", "title": "", "projects": []}
    lines = path.read_text(encoding="utf-8").splitlines()
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
        m = re.match(r'^title:\s*"?(.+?)"?\s*$', line)
        if m:
            fm["title"] = m.group(1).strip()
        m = re.match(r"^projects:\s*\[(.+)\]$", line)
        if m:
            def clean(p):
                p = p.strip().strip('"')
                return p[2:-2] if p.startswith("[[") and p.endswith("]]") else p
            fm["projects"] = [clean(p) for p in m.group(1).split(",") if clean(p)]
    return fm


def update_index(dir_path, index_path, wl_prefix, conv_entries, memory_path=None):
    file_lines = []
    items = sorted(dir_path.iterdir(), key=lambda x: x.name)

    for item in items:
        if item.name == "index.md":
            continue
        if item.is_dir():
            sub_index = item / "index.md"
            if sub_index.exists():
                sub_wl = f"{wl_prefix}/{item.name}"
                file_lines.append(f"- [[{sub_wl}/index|{item.name}]]")
                update_index(item, sub_index, sub_wl, [])
        elif item.suffix == ".md":
            base = item.stem
            file_lines.append(f"- [[{wl_prefix}/{base}]]")

    if not file_lines:
        file_lines = ["_No files yet._"]

    content = index_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    if memory_path is not None:
        status, next_items = parse_quick_status(memory_path)
        if status is not None:
            qs_lines = [f"**status:** {status}", ""]
            if next_items:
                qs_lines += ["**next:**"] + [f"- {item}" for item in next_items]
            else:
                qs_lines += ["**next:** —"]
            lines = set_section(lines, "quick status", qs_lines)

    lines = set_section(lines, "files", file_lines)

    joined = "\n".join(lines)
    if conv_entries or "## relevant conversations" in joined:
        if not conv_entries:
            conv_lines = ["_No classified conversations yet._"]
        else:
            sorted_convs = sorted(conv_entries, key=lambda e: e["updated"] or e["date"], reverse=True)
            conv_lines = [
                "| Date | Conversation |",
                "|------|--------------|",
            ] + [f"| {e['date']} | [[{e['base']}]] |" for e in sorted_convs]
        lines = set_section(lines, "relevant conversations", conv_lines)

    new_content = "\n".join(lines).rstrip() + "\n"
    index_path.write_text(new_content, encoding="utf-8")
    print(f"Updated: {index_path}")


def main():
    root = Path(__file__).parent.parent
    conv_dir = root / "_conversations"

    all_convs = []
    for f in conv_dir.rglob("*.md"):
        if f.name == "index.md":
            continue
        fm = parse_conv_frontmatter(f)
        all_convs.append((f.stem, fm))

    total = 0
    for ctx in ("personal", "professional", "public"):
        projects_dir = root / ctx / "projects"
        if not projects_dir.exists():
            continue
        for project_dir in sorted(projects_dir.iterdir()):
            if not project_dir.is_dir():
                continue
            project_index = project_dir / "index.md"
            if not project_index.exists():
                continue
            slug = project_dir.name
            conv_entries = [
                {"date": stem[:10], "updated": fm["updated"], "base": stem, "title": fm["title"] if fm["title"] else stem}
                for stem, fm in all_convs
                if slug in fm["projects"]
            ]
            update_index(project_dir, project_index, slug, conv_entries, project_dir / "_memory.md")
            total += 1

    print(f"Done. {total} project index(es) updated.")


if __name__ == "__main__":
    main()
