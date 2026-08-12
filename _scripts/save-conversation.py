#!/usr/bin/env python3
# Claude Code Stop/SessionEnd hook — reads hook JSON from stdin, saves conversation transcript
# to _conversations/ as a formatted markdown file.
import os
import sys
import re
import json
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta


def _load_dotenv(cwd: str | None) -> None:
    if not cwd:
        return
    env_file = Path(cwd) / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def _ntfy(base_url: str, topic: str, title: str, message: str) -> None:
    try:
        url = f"{base_url.rstrip('/')}/{topic}"
        req = urllib.request.Request(url, data=message.encode("utf-8"), method="POST")
        req.add_header("Title", title)
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


EVENT_MARKERS = {
    "🧠 [memory event]": "memory",
    "👤 [profile event]": "profile",
    "🗂️ [distill event]": "distill",
    "✅ [task event]": "task",
}

PROCESSED_MARKERS = {
    "🔁 [remember processed]": "memory",
    "🪪 [profile processed]": "profile",
    "📦 [distill processed]": "distill",
    "📋 [task processed]": "task",
}


def format_user_text(text):
    text = re.sub(
        r"(?s)<ide_opened_file>The user opened the file (.+?) in the IDE\.[^<]*</ide_opened_file>",
        r"🖥️ `Opened in IDE` \1",
        text,
    )
    text = re.sub(
        r"(?s)<ide_selection>The user selected the lines (\d+) to (\d+) from (.+?):\n.*?</ide_selection>",
        r"🖥️ `Selected in IDE` lines \1-\2 in \3",
        text,
    )
    text = re.sub(r"(?s)<system-reminder>.*?</system-reminder>", "", text)
    return text.strip()


def format_tool_call(part):
    n = part.get("name", "")
    i = part.get("input", {})
    if n == "Read":
        return f"🔧 `Read` {i.get('file_path', '')}"
    if n == "Write":
        return f"🔧 `Write` {i.get('file_path', '')}"
    if n == "Edit":
        return f"🔧 `Edit` {i.get('file_path', '')}"
    if n in ("Bash", "PowerShell"):
        d = i.get("description") or i.get("command", "")
        if len(d) > 100:
            d = d[:100] + "..."
        return f"🔧 `{n}` {d}"
    if n == "Grep":
        loc = f" in {i['path']}" if i.get("path") else ""
        return f"🔧 `Grep` {i.get('pattern', '')}{loc}"
    if n == "Glob":
        return f"🔧 `Glob` {i.get('pattern', '')}"
    if n == "Agent":
        d = i.get("description") or i.get("subagent_type", "")
        return f"🔧 `Agent` {d}"
    if n == "WebFetch":
        return f"🔧 `WebFetch` {i.get('url', '')}"
    if n == "WebSearch":
        return f"🔧 `WebSearch` {i.get('query', '')}"
    return f"🔧 `{n}`"


def extract_projects_from_transcript(msg_order, msg_data) -> list:
    found = []

    # 1. First user message: lines like "project: second-brain-setup"
    for uid in msg_order:
        msg = msg_data[uid]
        if msg["role"] == "user":
            for seg in msg.get("segments", []):
                if seg["t"] == "text":
                    for line in seg["v"].splitlines():
                        m = re.match(r"^\s*project:\s*(.+)$", line, re.IGNORECASE)
                        if m:
                            name = m.group(1).strip()
                            if name and name not in found:
                                found.append(name)
            break  # only first user message

    # 2. Tool call file paths: {context}/projects/{name}/
    contexts = {"personal", "professional", "public"}
    path_pattern = re.compile(
        r"(?:^|[/\\])(" + "|".join(contexts) + r")[/\\]projects[/\\]([^/\\]+)[/\\]",
        re.IGNORECASE,
    )
    for uid in msg_order:
        msg = msg_data[uid]
        if msg["role"] != "assistant":
            continue
        for seg in msg.get("segments", []):
            if seg["t"] == "tool":
                m = path_pattern.search(seg["v"])
                if m:
                    name = m.group(2)
                    if name and name not in found:
                        found.append(name)

    return found


def extract_events_from_transcript(msg_order, msg_data):
    events = []
    processed = []
    for uid in msg_order:
        msg = msg_data[uid]
        if msg["role"] != "assistant":
            continue
        for seg in msg.get("segments", []):
            if seg["t"] != "text":
                continue
            text = seg["v"]
            for marker, event_type in EVENT_MARKERS.items():
                if marker in text and event_type not in events:
                    events.append(event_type)
            for marker, proc_type in PROCESSED_MARKERS.items():
                if marker in text and proc_type not in processed:
                    processed.append(proc_type)
    return events, processed


def clean_project_name(p: str) -> str:
    p = p.strip().strip('"')
    return p[2:-2] if p.startswith("[[") and p.endswith("]]") else p


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    try:
        hook_data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    transcript_path = hook_data.get("transcript_path")
    cwd = hook_data.get("cwd")

    if not transcript_path or not Path(transcript_path).exists():
        sys.exit(0)

    lines = Path(transcript_path).read_text(encoding="utf-8").splitlines()

    ai_title = None
    msg_order = []
    msg_data = {}

    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        if entry.get("type") == "ai-title":
            ai_title = entry.get("aiTitle")

        if entry.get("type") == "user" and entry.get("message", {}).get("role") == "user":
            uid = "u_" + entry.get("uuid", "")
            if uid not in msg_data:
                msg_order.append(uid)
                msg_data[uid] = {"role": "user", "segments": [], "has_text": False}
            if not msg_data[uid]["has_text"] and entry["message"].get("content"):
                texts = [
                    p["text"]
                    for p in entry["message"]["content"]
                    if isinstance(p, dict) and p.get("type") == "text" and p.get("text")
                ]
                if texts:
                    combined = format_user_text("\n\n".join(texts))
                    if combined:
                        msg_data[uid]["segments"].append({"t": "text", "v": combined})
                        msg_data[uid]["has_text"] = True

        if (
            entry.get("type") == "assistant"
            and entry.get("message", {}).get("role") == "assistant"
            and entry.get("message", {}).get("content")
        ):
            aid = "a_" + entry["message"].get("id", "")
            if aid not in msg_data:
                msg_order.append(aid)
                msg_data[aid] = {
                    "role": "assistant",
                    "segments": [],
                    "has_text": False,
                    "seen_tool_ids": set(),
                }
            for part in entry["message"]["content"]:
                if not isinstance(part, dict) or "type" not in part:
                    continue
                if part["type"] == "text" and part.get("text") and not msg_data[aid]["has_text"]:
                    msg_data[aid]["segments"].append({"t": "text", "v": part["text"]})
                    msg_data[aid]["has_text"] = True
                elif part["type"] == "tool_use" and part.get("id"):
                    if part["id"] not in msg_data[aid]["seen_tool_ids"]:
                        msg_data[aid]["seen_tool_ids"].add(part["id"])
                        msg_data[aid]["segments"].append({"t": "tool", "v": format_tool_call(part)})

    if not ai_title:
        sys.exit(0)

    # Build output, merging consecutive assistant entries separated only by tool-result user messages
    output_entries = []
    for uid in msg_order:
        msg = msg_data[uid]
        if not msg["segments"]:
            continue
        last = output_entries[-1] if output_entries else None
        if msg["role"] == "assistant" and last and last["role"] == "assistant":
            last["segments"].extend(msg["segments"])
        else:
            output_entries.append({"role": msg["role"], "segments": list(msg["segments"])})

    session_id = Path(transcript_path).stem
    title = ai_title
    slug = re.sub(r" +", "-", re.sub(r"[^a-z0-9 ]", "", title.lower()))

    date = datetime.now().strftime("%Y-%m-%d")
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")

    conv_root = Path(cwd) / "_conversations"
    # Only save in repos that already have _conversations/ — prevents writing to
    # secondary roots in a multi-root workspace (e.g. a public repo).
    if not conv_root.exists():
        sys.exit(0)
    output_dir = conv_root / year / month
    output_dir.mkdir(parents=True, exist_ok=True)

    existing_projects = "[]"

    today = date
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    for f in list(conv_root.rglob(f"{today}-*.md")) + list(conv_root.rglob(f"{yesterday}-*.md")):
        fm = {}
        try:
            ex_lines = f.read_text(encoding="utf-8").splitlines()
            in_fm = False
            fm_count = 0
            fm_done = False
            for ln in ex_lines:
                stripped = ln.strip()
                if not fm_done and fm_count == 0 and stripped == "---":
                    in_fm = True
                    fm_count += 1
                    continue
                if in_fm and stripped == "---":
                    fm_done = True
                    break
                if in_fm:
                    m = re.match(r"^session:\s*(.+)$", ln)
                    if m:
                        fm["session"] = m.group(1).strip()
                    m = re.match(r"^date:\s*(.+)$", ln)
                    if m:
                        fm["date"] = m.group(1).strip()
                    m = re.match(r"^projects:\s*(.+)$", ln)
                    if m:
                        fm["projects"] = m.group(1).strip()
        except Exception:
            continue

        if fm.get("session") == session_id:
            date = fm.get("date", date)
            existing_projects = fm.get("projects", "[]")
            new_filename = f"{date}-{slug}.md"
            if f.name != new_filename:
                f.unlink()
            break

    # Normalize existing projects — strip [[...]] wrappers from old format
    try:
        proj_list = [clean_project_name(p) for p in json.loads(existing_projects) if isinstance(p, str) and p.strip()]
    except (json.JSONDecodeError, ValueError):
        proj_list = []

    extracted = extract_projects_from_transcript(msg_order, msg_data)
    for name in extracted:
        if name not in proj_list:
            proj_list.append(name)

    events, processed = extract_events_from_transcript(msg_order, msg_data)

    filename = f"{date}-{slug}.md"
    yaml_title = title.replace('"', '\\"')
    updated = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    parts = [
        "---",
        f"updated: {updated}",
        f'title: "{yaml_title}"',
        f"session: {session_id}",
        f"projects: {json.dumps(proj_list)}",
    ]
    if events:
        parts.append(f"events: {json.dumps(events)}")
    if processed:
        parts.append(f"processed: {json.dumps(processed)}")
    parts += [
        "---",
        "",
        f"# {title}",
        "",
    ]
    if proj_list:
        project_links = ", ".join(f"[[{p}/index|{p}]]" for p in proj_list)
        parts.append(f"**Projects:** {project_links}")
        parts.append("")

    for entry in output_entries:
        label = "### 💬 User" if entry["role"] == "user" else "### 🤖 Assistant"
        parts.append(label)
        parts.append("")
        for seg in entry["segments"]:
            parts.append(seg["v"])
            parts.append("")
        parts.append("---")
        parts.append("")

    output_path = output_dir / filename
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts))

    pending = [e for e in events if e not in processed]
    if pending and "--notify" in sys.argv:
        _load_dotenv(cwd)
        ntfy_url = os.environ.get("NTFY_URL", "")
        ntfy_topic = os.environ.get("NTFY_TOPIC", "second-brain")
        ntfy_on_events = os.environ.get("NTFY_ON_EVENTS", "true").lower() != "false"
        if ntfy_url and ntfy_on_events:
            session = Path(filename).stem
            _ntfy(
                ntfy_url, ntfy_topic,
                "📬 Second Brain: events pending",
                f"{session}: {', '.join(pending)} — run /remember",
            )


if __name__ == "__main__":
    main()
