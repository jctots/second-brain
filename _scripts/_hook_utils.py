#!/usr/bin/env python3
"""Shared utilities for Claude Code UserPromptSubmit hook scripts."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

CONTEXTS = ["personal", "professional", "public"]


def is_first_turn(transcript_path: str) -> bool:
    """Return True if no assistant entry exists yet in the transcript."""
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


def load_dotenv(root: Path) -> None:
    """Load .env from vault root into os.environ (setdefault — never overwrites)."""
    env_file = root / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def get_first_user_message(transcript_path: str) -> str | None:
    """Return text content of the first user message in the transcript."""
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


def get_ide_opened_file(transcript_path: str) -> str | None:
    """Return the file path from an IDE-opened-file annotation, if present."""
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
                            m = re.search(r"The user opened the file (.+?) in the IDE", block.get("text", ""))
                            if m:
                                return m.group(1).strip()
        except json.JSONDecodeError:
            continue
    return None


def find_project_from_file(cwd: Path, file_path: str) -> list[Path]:
    """Return project dir(s) inferred from an IDE-opened file path."""
    try:
        rel = Path(file_path).relative_to(cwd)
    except ValueError:
        return []
    parts = rel.parts
    if len(parts) >= 3 and parts[0] in CONTEXTS and parts[1] == "projects":
        project_dir = cwd / parts[0] / "projects" / parts[2]
        if project_dir.exists():
            return [project_dir]
    return []


def strip_ide_selection(message: str) -> str:
    """Remove <ide_selection>...</ide_selection> blocks from a message."""
    return re.sub(r"<ide_selection>.*?</ide_selection>", "", message, flags=re.DOTALL)


def find_projects_in_message(cwd: Path, message: str) -> list[Path]:
    """Return project dirs whose name appears in the message (hyphen or space form)."""
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
