#!/usr/bin/env python3
# Generates the project-status list, TOC sections, and system health block in dashboard.md.
# Preserves everything above the first --- separator (manual header).
# Run from repo root: python _scripts/generate-dashboard.py
import re
import shutil
from datetime import date
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
    """Return list of (wikilink, status, next_count) tuples for all project dirs."""
    results = []
    for item in sorted(para_dir.iterdir()):
        if not item.is_dir():
            continue
        wl = f"[[{item.name}/index|{item.name}]]"
        status, next_items = parse_snapshot(item / "_memory.md")
        results.append((wl, status, len(next_items)))
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


# ── system health ─────────────────────────────────────────────────────────────

def parse_pending_events(root):
    """Parse pending-events.md and return dict of event_type → count."""
    pending_file = root / "_conversations" / "pending-events.md"
    if not pending_file.exists():
        return {}
    counts = {}
    for line in pending_file.read_text(encoding="utf-8").splitlines():
        m = re.search(r"pending:\s*(.+)$", line)
        if m:
            for event in m.group(1).split(","):
                event = event.strip()
                if event:
                    counts[event] = counts.get(event, 0) + 1
    return counts


def count_inbox(root):
    """Return count of .md files in _inbox/."""
    inbox = root / "_inbox"
    if not inbox.exists():
        return 0
    return sum(1 for f in inbox.iterdir() if f.is_file() and f.suffix == ".md")


def _read_budget_warn(root) -> int:
    hard, warn_pct = 10_000, 80
    env_file = root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("HOOK_BUDGET_HARD="):
                try:
                    hard = int(line.split("=", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("HOOK_BUDGET_WARN_PCT="):
                try:
                    warn_pct = int(line.split("=", 1)[1].strip())
                except ValueError:
                    pass
    return int(hard * warn_pct / 100)


def check_hook_budget(root):
    """Return list of (display_path, char_count, is_warn) for files exceeding the 5k target."""
    TARGET = 5_000
    WARN = _read_budget_warn(root)
    flagged = []

    for name in ("about.md", "corrections.md"):
        f = root / "_self" / name
        if f.exists():
            size = len(f.read_text(encoding="utf-8"))
            if size > TARGET:
                flagged.append((f"_self/{name}", size, size > WARN))

    for ctx in ("personal", "professional", "public"):
        projects_dir = root / ctx / "projects"
        if not projects_dir.exists():
            continue
        for project_dir in sorted(projects_dir.iterdir()):
            if not project_dir.is_dir():
                continue
            for fname in ("CLAUDE.md", "_memory.md"):
                f = project_dir / fname
                if f.exists():
                    size = len(f.read_text(encoding="utf-8"))
                    if size > TARGET:
                        flagged.append((f"{ctx}/projects/{project_dir.name}/{fname}", size, size > WARN))

    return flagged


def read_rag_status(root):
    """Return ('ok'|'error'|'unknown', details_str)."""
    status_file = root / ".rag-status"
    if not status_file.exists():
        return "unknown", ""
    parts = status_file.read_text(encoding="utf-8").strip().split("|", 2)
    if parts[0] == "error" and len(parts) == 3:
        return "error", f"unavailable since {parts[1]} ({parts[2]})"
    if parts[0] == "ok":
        return "ok", ""
    return "unknown", ""


def generate_health_block(root):
    """Return lines for the ## ⚡ System Health section."""
    lines = ["## ⚡ System Health", ""]
    issues = []
    ok_parts = []

    event_counts = parse_pending_events(root)
    if event_counts:
        parts = [f"{v} {k}" for k, v in sorted(event_counts.items())]
        issues.append(f"📬 **Pending events:** {' · '.join(parts)} — run `/maintain` option 3")
    else:
        ok_parts.append("📬 no pending events")

    inbox_count = count_inbox(root)
    if inbox_count > 0:
        noun = "item" if inbox_count == 1 else "items"
        issues.append(f"📦 **Inbox:** {inbox_count} {noun} — run `/maintain` option 2")
    else:
        ok_parts.append("📦 inbox empty")

    flagged = check_hook_budget(root)
    warn_files = [(p, s) for p, s, is_warn in flagged if is_warn]
    over_target = [(p, s) for p, s, is_warn in flagged if not is_warn]
    if warn_files:
        for p, s in warn_files:
            issues.append(f"⚠️ **Budget:** `{p}` {s:,} chars — run `/maintain` option 4")
    elif over_target:
        issues.append(f"📊 **Budget:** {len(over_target)} file(s) over 5k target — run `/maintain` option 4")
    else:
        ok_parts.append("📊 budget OK")

    rag_state, rag_detail = read_rag_status(root)
    if rag_state == "error":
        issues.append(f"🔍 **RAG:** {rag_detail}")
    elif rag_state == "unknown":
        ok_parts.append("🔍 RAG unconfigured")
    else:
        ok_parts.append("🔍 RAG OK")

    if issues:
        lines.extend(issues)
    else:
        lines.append(" · ".join(ok_parts))

    return lines


# ── TOC ───────────────────────────────────────────────────────────────────────

CTX_EMOJI = {"personal": "🏠", "professional": "💼", "public": "🌐"}
PARA_EMOJI = {"projects": "📋", "areas": "🗂️", "resources": "📚"}
PARA_LABEL = {"projects": "Projects", "areas": "Areas", "resources": "Resources"}


def generate_toc(root):
    lines = []
    for ctx in ("personal", "professional", "public"):
        emoji = CTX_EMOJI[ctx]
        lines.append(f"## {emoji} {ctx.capitalize()}")
        lines.append("")
        for para in ("projects", "areas", "resources"):
            pe = PARA_EMOJI[para]
            pl = PARA_LABEL[para]
            para_dir = root / ctx / para
            if not para_dir.exists():
                lines.append(f"{pe} **{pl}:** —")
                lines.append("")
                continue

            if para == "projects":
                entries = collect_projects(para_dir)
                if not entries:
                    lines.append(f"{pe} **{pl}:** —")
                    lines.append("")
                    continue
                lines.append(f"{pe} **{pl}:**")
                for wl, status, next_count in entries:
                    suffix = f" — {status}" if status else ""
                    if next_count > 0:
                        suffix += f" · {next_count} open"
                    lines.append(f"- {wl}{suffix}")
                lines.append("")

            elif para == "resources":
                entries = collect_resources(para_dir)
                if not entries:
                    lines.append(f"{pe} **{pl}:** —")
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
                lines.append(f"{pe} **{pl}:** {' · '.join(tag_links) if tag_links else '—'}")
                lines.append("")

            else:  # areas
                items = collect_flat(para_dir)
                lines.append(f"{pe} **{pl}:** {' · '.join(items) if items else '—'}")
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
    health_lines = generate_health_block(root)
    toc_lines = generate_toc(root)

    new_lines = (
        manual_header
        + ["", "---", ""]
        + health_lines
        + ["", "---", ""]
        + toc_lines
    )

    dashboard.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    print("Updated: dashboard.md")


if __name__ == "__main__":
    main()
