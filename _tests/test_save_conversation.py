#!/usr/bin/env python3
"""T3 — Tests for save-conversation.py"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "_scripts"
REPO = Path(__file__).parent.parent


def load_script(name):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_").replace(".", "_"), path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_sc = load_script("save-conversation.py")


def run_script(stdin_data, cwd=None):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "save-conversation.py")],
        input=stdin_data,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd or str(REPO),
    )
    return result.returncode, result.stdout


def make_transcript(path, entries):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def basic_transcript(title="My Session", user_text="Hello", assistant_text="Hi there"):
    return [
        {"type": "ai-title", "aiTitle": title},
        {
            "type": "user",
            "uuid": "u1",
            "message": {"role": "user", "content": [{"type": "text", "text": user_text}]},
        },
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "id": "a1",
                "content": [{"type": "text", "text": assistant_text}],
            },
        },
    ]


# --- T3.1-T3.8: format_user_text ---

class TestFormatUserText(unittest.TestCase):

    def test_t3_1_plain_text_unchanged(self):
        assert _sc.format_user_text("hello world") == "hello world"

    def test_t3_2_system_reminder_removed(self):
        text = "before\n<system-reminder>SECRET</system-reminder>\nafter"
        result = _sc.format_user_text(text)
        assert "SECRET" not in result
        assert "before" in result
        assert "after" in result

    def test_t3_3_ide_opened_file_replaced(self):
        text = "<ide_opened_file>The user opened the file /path/to/file.md in the IDE.</ide_opened_file>"
        result = _sc.format_user_text(text)
        assert "`Opened in IDE`" in result
        assert "/path/to/file.md" in result

    def test_t3_4_ide_selection_replaced(self):
        text = "<ide_selection>The user selected the lines 5 to 10 from /path/file.py:\nsome code\n</ide_selection>"
        result = _sc.format_user_text(text)
        assert "`Selected in IDE`" in result
        assert "lines 5-10" in result
        assert "/path/file.py" in result

    def test_t3_5_multiple_system_reminders_removed(self):
        text = "<system-reminder>A</system-reminder>middle<system-reminder>B</system-reminder>"
        result = _sc.format_user_text(text)
        assert "A" not in result
        assert "B" not in result

    def test_t3_6_ide_and_system_reminder_independent(self):
        text = (
            "<ide_opened_file>The user opened the file /f.md in the IDE.</ide_opened_file>\n"
            "<system-reminder>SECRET</system-reminder>"
        )
        result = _sc.format_user_text(text)
        assert "SECRET" not in result
        assert "/f.md" in result

    def test_t3_7_empty_string(self):
        assert _sc.format_user_text("") == ""

    def test_t3_8_multiline_system_reminder(self):
        text = "<system-reminder>\nline one\nline two\n</system-reminder>"
        result = _sc.format_user_text(text)
        assert "line one" not in result
        assert "line two" not in result


# --- T3.9-T3.20: extract_events_from_transcript ---

def _msg(role, text=None, tool=None):
    segments = []
    if text:
        segments.append({"t": "text", "v": text})
    if tool:
        segments.append({"t": "tool", "v": tool})
    return {"role": role, "segments": segments}


class TestExtractEvents(unittest.TestCase):

    def _run(self, entries):
        order = [str(i) for i in range(len(entries))]
        data = {str(i): e for i, e in enumerate(entries)}
        return _sc.extract_events_from_transcript(order, data)

    def test_t3_9_memory_marker(self):
        events, _ = self._run([_msg("assistant", "🧠 [memory event]: something")])
        assert "memory" in events

    def test_t3_10_profile_marker(self):
        events, _ = self._run([_msg("assistant", "👤 [profile event]: something")])
        assert "profile" in events

    def test_t3_11_distill_marker(self):
        events, _ = self._run([_msg("assistant", "🗂️ [distill event]: something")])
        assert "distill" in events

    def test_t3_12_task_marker(self):
        events, _ = self._run([_msg("assistant", "✅ [task event]: something")])
        assert "task" in events

    def test_t3_13_remember_processed(self):
        _, processed = self._run([_msg("assistant", "🔁 [remember processed]")])
        assert "memory" in processed

    def test_t3_14_profile_processed(self):
        _, processed = self._run([_msg("assistant", "🪪 [profile processed]")])
        assert "profile" in processed

    def test_t3_15_distill_processed(self):
        _, processed = self._run([_msg("assistant", "📦 [distill processed]")])
        assert "distill" in processed

    def test_t3_16_task_processed(self):
        _, processed = self._run([_msg("assistant", "📋 [task processed]")])
        assert "task" in processed

    def test_t3_17_deduped_across_messages(self):
        events, _ = self._run([
            _msg("assistant", "🧠 [memory event]: first"),
            _msg("assistant", "🧠 [memory event]: second"),
        ])
        assert events.count("memory") == 1

    def test_t3_18_user_turn_not_captured(self):
        events, _ = self._run([_msg("user", "🧠 [memory event]: user said")])
        assert "memory" not in events

    def test_t3_19_emoji_only_not_matched(self):
        events, _ = self._run([_msg("assistant", "🧠 standalone emoji")])
        assert "memory" not in events

    def test_t3_20_no_markers(self):
        events, processed = self._run([_msg("assistant", "nothing special")])
        assert events == []
        assert processed == []


# --- T3.21-T3.26: extract_projects_from_transcript ---

class TestExtractProjects(unittest.TestCase):

    def _run(self, entries):
        order = [str(i) for i in range(len(entries))]
        data = {str(i): e for i, e in enumerate(entries)}
        return _sc.extract_projects_from_transcript(order, data)

    def test_t3_21_project_line_in_first_user_message(self):
        result = self._run([_msg("user", "project: my-project\nhello")])
        assert "my-project" in result

    def test_t3_22_tool_path_personal_projects(self):
        result = self._run([
            _msg("user", "hello"),
            _msg("assistant", tool="> `Read` /vault/personal/projects/my-project/file.md"),
        ])
        assert "my-project" in result

    def test_t3_23_deduped(self):
        result = self._run([
            _msg("user", "project: my-project"),
            _msg("assistant", tool="> `Read` /vault/personal/projects/my-project/file.md"),
        ])
        assert result.count("my-project") == 1

    def test_t3_24_project_line_not_in_first_user_message(self):
        result = self._run([
            _msg("user", "hello"),
            _msg("user", "project: my-project"),
        ])
        assert "my-project" not in result

    def test_t3_25_no_project_line_no_tool_paths(self):
        result = self._run([_msg("user", "hello"), _msg("assistant", "world")])
        assert result == []

    def test_t3_26_areas_not_matched(self):
        result = self._run([
            _msg("user", "hello"),
            _msg("assistant", tool="> `Read` /vault/personal/areas/my-area/file.md"),
        ])
        assert "my-area" not in result


# --- T3.27-T3.30: clean_project_name ---

class TestCleanProjectName(unittest.TestCase):

    def test_t3_27_plain_name(self):
        assert _sc.clean_project_name("my-project") == "my-project"

    def test_t3_28_wikilink_format(self):
        assert _sc.clean_project_name("[[my-project]]") == "my-project"

    def test_t3_29_whitespace_stripped(self):
        assert _sc.clean_project_name("  my-project  ") == "my-project"

    def test_t3_30_quoted(self):
        assert _sc.clean_project_name('"my-project"') == "my-project"


# --- T3.31-T3.39: main() via subprocess ---

class TestSaveConversationMain(unittest.TestCase):

    def _run(self, hook_data, transcript_entries=None, tmp_dir=None):
        d = tmp_dir
        t = Path(d) / "transcript.jsonl"
        if transcript_entries is not None:
            make_transcript(t, transcript_entries)
        hook = dict(hook_data)
        if "transcript_path" not in hook:
            hook["transcript_path"] = str(t)
        if "cwd" not in hook:
            cwd = Path(d)
            (cwd / "_conversations").mkdir(exist_ok=True)
            hook["cwd"] = str(cwd)
        return run_script(json.dumps(hook))

    def test_t3_31_valid_transcript_written(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            (cwd / "_conversations").mkdir()
            t = Path(d) / "t.jsonl"
            make_transcript(t, basic_transcript("My Session", "project: test-proj", "Answer"))
            hook = json.dumps({"transcript_path": str(t), "cwd": str(cwd)})
            rc, _ = run_script(hook)
            assert rc == 0
            files = list((cwd / "_conversations").rglob("*.md"))
            assert len(files) == 1
            text = files[0].read_text(encoding="utf-8")
            assert "My Session" in text
            assert "session:" in text

    def test_t3_32_existing_file_same_session_date_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            conv = cwd / "_conversations" / "2026" / "01"
            conv.mkdir(parents=True)
            session_id = "abc123"
            t = Path(d) / f"{session_id}.jsonl"
            make_transcript(t, basic_transcript("Rename Me"))
            # Pre-existing file with same session ID but old title slug
            old_file = conv / "2026-01-01-old-title.md"
            old_file.write_text(
                f"---\nsession: {session_id}\ndate: 2026-01-01\nprojects: []\n---\n# Old\n",
                encoding="utf-8",
            )
            hook = json.dumps({"transcript_path": str(t), "cwd": str(cwd)})
            rc, _ = run_script(hook)
            assert rc == 0
            files = list((cwd / "_conversations").rglob("*.md"))
            texts = [f.read_text(encoding="utf-8") for f in files]
            assert any("2026-01-01" in f.name for f in files), "date should be preserved"

    def test_t3_33_empty_stdin(self):
        rc, _ = run_script("")
        assert rc == 0

    def test_t3_34_invalid_json_stdin(self):
        rc, _ = run_script("not json")
        assert rc == 0

    def test_t3_35_missing_transcript_path_key(self):
        rc, _ = run_script(json.dumps({"cwd": str(REPO)}))
        assert rc == 0

    def test_t3_36_transcript_does_not_exist(self):
        with tempfile.TemporaryDirectory() as d:
            hook = json.dumps({"transcript_path": str(Path(d) / "ghost.jsonl"), "cwd": str(d)})
            rc, _ = run_script(hook)
            assert rc == 0

    def test_t3_37_no_ai_title(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            (cwd / "_conversations").mkdir()
            t = Path(d) / "t.jsonl"
            make_transcript(t, [
                {"type": "user", "uuid": "u1",
                 "message": {"role": "user", "content": [{"type": "text", "text": "hello"}]}},
            ])
            hook = json.dumps({"transcript_path": str(t), "cwd": str(cwd)})
            rc, _ = run_script(hook)
            assert rc == 0
            assert list((cwd / "_conversations").rglob("*.md")) == []

    def test_t3_38_no_conversations_dir(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript(t, basic_transcript("Test"))
            hook = json.dumps({"transcript_path": str(t), "cwd": str(d)})
            rc, _ = run_script(hook)
            assert rc == 0
            assert not (Path(d) / "_conversations").exists()

    def test_t3_39_zero_text_segments_no_crash(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            (cwd / "_conversations").mkdir()
            t = Path(d) / "t.jsonl"
            make_transcript(t, [{"type": "ai-title", "aiTitle": "Empty Session"}])
            hook = json.dumps({"transcript_path": str(t), "cwd": str(cwd)})
            rc, _ = run_script(hook)
            assert rc == 0


# --- T3.40-T3.42: ntfy on unprocessed events ---

class TestNtfyOnUnprocessedEvents(unittest.TestCase):

    def _hook(self, tmp_dir, entries):
        cwd = Path(tmp_dir)
        (cwd / "_conversations").mkdir(exist_ok=True)
        t = cwd / "t.jsonl"
        make_transcript(t, entries)
        return json.dumps({"transcript_path": str(t), "cwd": str(cwd)})

    def _run(self, hook_json, env=None, notify=False):
        argv = ["save-conversation.py"] + (["--notify"] if notify else [])
        with unittest.mock.patch("sys.stdin", io.StringIO(hook_json)):
            with unittest.mock.patch("sys.argv", argv):
                with unittest.mock.patch.dict(os.environ, env or {}, clear=True):
                    with unittest.mock.patch("urllib.request.urlopen") as mock_open:
                        try:
                            _sc.main()
                        except SystemExit:
                            pass
                        return mock_open.call_count

    def test_t3_40_ntfy_called_when_events_unprocessed_and_url_set(self):
        with tempfile.TemporaryDirectory() as d:
            entries = basic_transcript(
                "Unprocessed Events",
                "project: test",
                "🧠 [memory event]: something important",
            )
            count = self._run(
                self._hook(d, entries),
                {"NTFY_URL": "http://ntfy.example.com", "NTFY_TOPIC": "test"},
                notify=True,
            )
            assert count == 1

    def test_t3_41_ntfy_not_called_when_all_events_processed(self):
        with tempfile.TemporaryDirectory() as d:
            entries = basic_transcript(
                "Processed Events",
                "project: test",
                "🧠 [memory event]: something\n🔁 [remember processed]",
            )
            count = self._run(
                self._hook(d, entries),
                {"NTFY_URL": "http://ntfy.example.com", "NTFY_TOPIC": "test"},
                notify=True,
            )
            assert count == 0

    def test_t3_42_ntfy_skipped_silently_when_url_not_set(self):
        with tempfile.TemporaryDirectory() as d:
            entries = basic_transcript(
                "No URL Session",
                "project: test",
                "🧠 [memory event]: something important",
            )
            count = self._run(self._hook(d, entries), {}, notify=True)
            assert count == 0


# --- Smoke test ---

class TestSmoke(unittest.TestCase):

    def test_smoke_save_conversation(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            (cwd / "_conversations").mkdir()
            t = Path(d) / "t.jsonl"
            make_transcript(t, basic_transcript("Smoke Test"))
            hook = json.dumps({"transcript_path": str(t), "cwd": str(cwd)})
            rc, _ = run_script(hook)
            assert rc == 0


if __name__ == "__main__":
    unittest.main(verbosity=2)
