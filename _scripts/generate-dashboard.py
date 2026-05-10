#!/usr/bin/env python3
# Generates the project-status table and TOC sections in dashboard.md.
# Preserves everything above the first --- separator (manual header).
# Run from repo root: python _scripts/generate-dashboard.py
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


def generate_project_status(root):
    rows = []
    for ctx in ("personal", "professional", "public"):
        projects_dir = root / ctx / "projects"
        if not projects_dir.exists():
            continue
        for project_dir in sorted(projects_dir.iterdir()):
            if not project_dir.is_dir():
                continue
            status, next_items = parse_quick_status(project_dir / "_memory.md")
            if status is None:
                continue
            slug = project_dir.name
            wl = f"[[{slug}/index|{slug}]]"
            next_str = next_items[0] if next_items else "—"
            rows.append(f"| {wl} | {status} | {next_str} |")

    if not rows:
        return ["## active projects", "", "_No active projects with quick status._"]

    return (
        ["## active projects", ""]
        + ["| Project | Status | Next |", "|---------|--------|------|"]
        + rows
    )


def parse_frontmatter_tags(file_path):
    lines = file_path.read_text(encoding="utf-8").splitlines()
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
        m = re.match(r"^tags:\s*\[(.*)]\s*$", line)
        if m:
            raw = m.group(1).strip()
            if raw:
                return [t.strip().strip('"').strip("'").lstrip("#") for t in raw.split(",") if t.strip()]
    return []


def collect_resources(para_dir):
    """Return list of (wikilink, file_path) for all resource files."""
    results = []
    for item in sorted(para_dir.iterdir()):
        if item.is_dir():
            if (item / "index.md").exists():
                results.append((f"[[{item.name}/index|{item.name}]]", None))
            else:
                for subitem in sorted(item.iterdir()):
                    if subitem.is_file() and subitem.suffix == ".md":
                        results.append((f"[[{item.name}/{subitem.stem}]]", subitem))
        elif item.is_file() and item.suffix == ".md" and item.name != "index.md":
            results.append((f"[[{item.stem}]]", item))
    return results


def collect_flat(para_dir):
    """Return flat wikilink list for projects and areas."""
    items = []
    for item in sorted(para_dir.iterdir()):
        if item.is_dir():
            if (item / "index.md").exists():
                items.append(f"[[{item.name}/index|{item.name}]]")
            else:
                for subitem in sorted(item.iterdir()):
                    if subitem.is_file() and subitem.suffix == ".md":
                        items.append(f"[[{item.name}/{subitem.stem}]]")
        elif item.is_file() and item.suffix == ".md" and item.name != "index.md":
            items.append(f"[[{item.stem}]]")
    return items


def generate_toc(root):
    lines = []
    for ctx in ("personal", "professional", "public"):
        lines.append(f"## {ctx}")
        lines.append("")
        for para in ("projects", "areas", "resources"):
            para_dir = root / ctx / para
            if not para_dir.exists():
                lines.append(f"**{para}:** —")
                lines.append("")
                continue

            if para == "resources":
                entries = collect_resources(para_dir)
                if not entries:
                    lines.append("**resources:** —")
                    lines.append("")
                    continue
                # Group by tag; untagged collected separately
                tag_map = {}
                untagged = []
                for wl, fp in entries:
                    tags = parse_frontmatter_tags(fp) if fp else []
                    if tags:
                        for tag in tags:
                            tag_map.setdefault(tag, []).append(wl)
                    else:
                        untagged.append(wl)
                cluster_tags = {t: wls for t, wls in tag_map.items() if len(wls) >= 2}
                clustered_wls = {wl for wls in cluster_tags.values() for wl in wls}
                other = sorted(set(untagged) | {wl for wls in tag_map.values() for wl in wls if wl not in clustered_wls})
                lines.append("**resources:**")
                for tag in sorted(cluster_tags):
                    lines.append(f"- `#{tag}` — {' · '.join(cluster_tags[tag])}")
                if other:
                    lines.append(f"- `#other` — {' · '.join(other)}")
            else:
                items = collect_flat(para_dir)
                lines.append(f"**{para}:** {' · '.join(items) if items else '—'}")

            lines.append("")
        lines.append("---")
        lines.append("")

    # Remove trailing separator and blanks
    while lines and lines[-1] in ("", "---"):
        lines.pop()

    return lines


def main():
    root = Path(__file__).parent.parent
    dashboard = root / "dashboard.md"
    content = dashboard.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Everything above the first --- is the manual header
    sep_idx = next((i for i, l in enumerate(lines) if l.strip() == "---"), len(lines))
    manual_header = lines[:sep_idx]
    while manual_header and not manual_header[-1].strip():
        manual_header.pop()

    status_lines = generate_project_status(root)
    toc_lines = generate_toc(root)

    new_lines = (
        manual_header
        + ["", "---", ""]
        + status_lines
        + ["", "---", ""]
        + toc_lines
    )

    dashboard.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    print("Updated: dashboard.md")


if __name__ == "__main__":
    main()
