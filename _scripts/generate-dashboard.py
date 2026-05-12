#!/usr/bin/env python3
# Generates the project-status list and TOC sections in dashboard.md.
# Preserves everything above the first --- separator (manual header).
# Run from repo root: python _scripts/generate-dashboard.py
import re
import shutil
from datetime import date
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
        if item.is_dir() and item.name == "tags":
            continue
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
    """Return flat wikilink list for areas."""
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


def collect_projects(para_dir):
    """Return list of (wikilink, status) tuples for all project dirs."""
    results = []
    for item in sorted(para_dir.iterdir()):
        if not item.is_dir():
            continue
        wl = f"[[{item.name}/index|{item.name}]]"
        status, _ = parse_quick_status(item / "_memory.md")
        results.append((wl, status))
    return results


def generate_tag_pages(root):
    """Write per-tag resource index pages under {ctx}/resources/tags/. Wipes stale pages."""
    for ctx in ("personal", "professional", "public"):
        resources_dir = root / ctx / "resources"
        tags_dir = resources_dir / "tags"

        if not resources_dir.exists():
            continue

        entries = collect_resources(resources_dir)
        tag_map = {}
        for wl, fp in entries:
            tags = parse_frontmatter_tags(fp) if fp else []
            for tag in tags:
                tag_map.setdefault(tag, []).append(wl)

        existing_created = {}
        if tags_dir.exists():
            for existing_page in tags_dir.glob("*.md"):
                m = re.search(r"^created:\s*(\S+)", existing_page.read_text(encoding="utf-8"), re.MULTILINE)
                if m:
                    existing_created[existing_page.stem] = m.group(1)
            shutil.rmtree(tags_dir)

        if not tag_map:
            continue

        tags_dir.mkdir(parents=True)
        today = date.today().isoformat()
        for tag, wls in sorted(tag_map.items()):
            page = tags_dir / f"{tag}.md"
            created = existing_created.get(tag, today)
            lines = [
                "---",
                f"context: {ctx}",
                "para: resources",
                f"tags: [{tag}]",
                f"created: {created}",
                "---",
                "",
                f"# #{tag}",
                "",
                "[[dashboard|⬅️ Dashboard]]",
                "",
            ]
            for wl in sorted(wls):
                lines.append(f"- {wl}")
            lines.append("")
            page.write_text("\n".join(lines), encoding="utf-8")

        print(f"Generated {len(tag_map)} tag pages in {ctx}/resources/tags/")


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

            if para == "projects":
                entries = collect_projects(para_dir)
                if not entries:
                    lines.append("**projects:** —")
                    lines.append("")
                    continue
                lines.append("**projects:**")
                for wl, status in entries:
                    suffix = f" — {status}" if status else ""
                    lines.append(f"- {wl}{suffix}")
                lines.append("")

            elif para == "resources":
                entries = collect_resources(para_dir)
                if not entries:
                    lines.append("**resources:** —")
                    lines.append("")
                    continue
                tag_map = {}
                untagged = []
                for wl, fp in entries:
                    tags = parse_frontmatter_tags(fp) if fp else []
                    if tags:
                        for tag in tags:
                            tag_map.setdefault(tag, []).append(wl)
                    else:
                        untagged.append(wl)
                tag_links = [f"[[{ctx}/resources/tags/{t}|#{t}]]" for t in sorted(tag_map)]
                if untagged:
                    tag_links.extend(untagged)
                lines.append(f"**resources:** {' · '.join(tag_links) if tag_links else '—'}")
                lines.append("")

            else:  # areas
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

    generate_tag_pages(root)
    toc_lines = generate_toc(root)

    new_lines = (
        manual_header
        + ["", "---", ""]
        + toc_lines
    )

    dashboard.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    print("Updated: dashboard.md")


if __name__ == "__main__":
    main()
