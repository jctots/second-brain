#!/usr/bin/env python3
# Generates "## files", "## relevant conversations", "## snapshot", and "## next actions" sections in all project index.md files.
# Run from repo root: python _scripts/generate-project-indices.py
import re
from pathlib import Path


def parse_snapshot(memory_path):
    if not memory_path.exists():
        return None, []
    lines = memory_path.read_text(encoding="utf-8").splitlines()
    snapshot = None
    next_items = []
    current_section = None
    for line in lines:
        if re.match(r"^## Snapshot\s*$", line, re.IGNORECASE):
            current_section = "snapshot"
            continue
        if re.match(r"^## Next Actions\s*$", line, re.IGNORECASE):
            current_section = "next"
            continue
        if re.match(r"^## ", line):
            current_section = None
            continue
        if current_section == "snapshot" and line.strip() and snapshot is None:
            snapshot = line.strip()
        elif current_section == "next" and line.startswith("- "):
            next_items.append(line[2:].strip())
    return snapshot, next_items


SECTIONS = {
    "snapshot": "⚡ Snapshot",
    "next actions": "📌 Next Actions",
    "files": "📁 Files",
    "relevant conversations": "💬 Relevant Conversations",
}
LEGACY_SECTIONS = ["quick status"]


def remove_section(lines, keyword):
    # Matches heading by keyword, ignoring leading emoji or capitalization
    for i, line in enumerate(lines):
        if re.match(r"^## ", line) and re.search(re.escape(keyword), line, re.IGNORECASE):
            sec_end = len(lines)
            for j in range(i + 1, len(lines)):
                if re.match(r"^## ", lines[j]):
                    sec_end = j
                    break
            before = lines[:i]
            while before and not before[-1].strip():
                before = before[:-1]
            after = lines[sec_end:]
            return before + ([""] + after if after else after)
    return lines


def append_section(lines, heading, new_lines):
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines + [""] + [f"## {heading}", ""] + list(new_lines)



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


def _has_md_content(dir_path):
    """Return True if dir_path contains any .md files (non-index) or non-_ subdirs with content."""
    for item in dir_path.iterdir():
        if item.is_file() and item.suffix == ".md" and item.name != "index.md":
            return True
        if item.is_dir() and not item.name.startswith("_"):
            return True
    return False


def _ensure_subdir_index(sub_dir, wl_prefix):
    """Generate a minimal index.md stub for sub_dir if one doesn't exist."""
    sub_index = sub_dir / "index.md"
    if sub_index.exists():
        return sub_index
    project_name = wl_prefix.split("/")[0]
    stub = f"# {sub_dir.name}\n\n[[{project_name}/index|⬅️ {project_name}]]\n"
    sub_index.write_text(stub, encoding="utf-8")
    print(f"Generated: {sub_index}")
    return sub_index


def update_index(dir_path, index_path, wl_prefix, conv_entries, memory_path=None):
    file_lines = []
    items = sorted(dir_path.iterdir(), key=lambda x: x.name)

    for item in items:
        if item.name == "index.md":
            continue
        if item.is_dir():
            if item.name.startswith("_"):
                continue
            sub_index = item / "index.md"
            if not sub_index.exists() and _has_md_content(item):
                sub_index = _ensure_subdir_index(item, wl_prefix)
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

    has_conv_section = bool(re.search(r"^## .*relevant conversations\s*$", content, re.MULTILINE | re.IGNORECASE))

    # Compute snapshot and next actions before stripping
    snap_lines = None
    next_lines = None
    if memory_path is not None:
        snapshot, next_items = parse_snapshot(memory_path)
        if snapshot is not None:
            snap_lines = [snapshot]
        if snapshot is not None:
            next_lines = [f"- 🔲 {item}" for item in next_items] if next_items else ["_No open actions._"]

    # Strip all managed sections (including legacy), then re-append in enforced order
    for keyword in list(SECTIONS.keys()) + LEGACY_SECTIONS:
        lines = remove_section(lines, keyword)

    if snap_lines is not None:
        lines = append_section(lines, SECTIONS["snapshot"], snap_lines)
    if next_lines is not None:
        lines = append_section(lines, SECTIONS["next actions"], next_lines)
    lines = append_section(lines, SECTIONS["files"], file_lines)

    if conv_entries or has_conv_section:
        if conv_entries:
            sorted_convs = sorted(conv_entries, key=lambda e: e["updated"] or e["date"], reverse=True)
            conv_lines = [
                "| Date | Conversation |",
                "|------|--------------|",
            ] + [f"| {e['date']} | [[{e['base']}]] |" for e in sorted_convs]
        else:
            conv_lines = ["_No classified conversations yet._"]
        lines = append_section(lines, SECTIONS["relevant conversations"], conv_lines)

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
