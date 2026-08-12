#!/usr/bin/env python3
"""T2 — Tests for inject-context-claude.py and inject-context-memory.py.
Utility functions (is_first_turn, get_first_user_message, etc.) live in _hook_utils.py and are tested here
via the inject scripts that import them.

T2.7-T2.14 covered inject-profile.py and inject-corrections.py, retired when `_self/about.md`
and `_self/corrections.md` moved to `@` imports in root CLAUDE.md. The numbers are left
vacant rather than reused — T#.# identifiers are stable (D126)."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
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


_context = load_script("inject-context-claude.py")


def make_transcript(entries, path):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def run_script(script_name, stdin_data):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / script_name)],
        input=stdin_data,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.returncode, result.stdout


# --- T2.1-T2.6: is_first_turn ---

class TestIsFirstTurn(unittest.TestCase):

    def test_t2_1_no_transcript(self):
        assert _context.is_first_turn("/nonexistent/path/x.jsonl") is True

    def test_t2_2_only_user_entries(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript([{"type": "user"}], t)
            assert _context.is_first_turn(str(t)) is True

    def test_t2_3_has_assistant_entry(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript([{"type": "user"}, {"type": "assistant"}], t)
            assert _context.is_first_turn(str(t)) is False

    def test_t2_4_empty_transcript(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            t.write_text("", encoding="utf-8")
            assert _context.is_first_turn(str(t)) is True

    def test_t2_5_malformed_json_lines(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            t.write_text('not json\n{"type":"user"}\n', encoding="utf-8")
            assert _context.is_first_turn(str(t)) is True

    def test_t2_6_blank_lines(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            t.write_text('\n\n{"type":"user"}\n\n', encoding="utf-8")
            assert _context.is_first_turn(str(t)) is True


# --- T2.15-T2.19: get_first_user_message ---

class TestGetFirstUserMessage(unittest.TestCase):

    def test_t2_15_dict_message_text_block(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript([{
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": "hello world"}]},
            }], t)
            assert _context.get_first_user_message(str(t)) == "hello world"

    def test_t2_16_string_message(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript([{"type": "user", "message": "direct string"}], t)
            assert _context.get_first_user_message(str(t)) == "direct string"

    def test_t2_17_no_transcript(self):
        assert _context.get_first_user_message("/nonexistent.jsonl") is None

    def test_t2_18_no_user_entries(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript([{"type": "assistant"}], t)
            assert _context.get_first_user_message(str(t)) is None

    def test_t2_19_malformed_lines_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            t.write_text('bad json\n{"type":"user","message":"hi"}\n', encoding="utf-8")
            assert _context.get_first_user_message(str(t)) == "hi"


# --- T2.20-T2.22: get_ide_opened_file ---

class TestGetIdeOpenedFile(unittest.TestCase):

    def test_t2_20_ide_annotation(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            text = "The user opened the file /path/to/file.md in the IDE."
            make_transcript([{
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": text}]},
            }], t)
            assert _context.get_ide_opened_file(str(t)) == "/path/to/file.md"

    def test_t2_21_no_annotation(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript([{
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": "nothing here"}]},
            }], t)
            assert _context.get_ide_opened_file(str(t)) is None

    def test_t2_22_unusual_absolute_path(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            fp = "/unusual/deep/nested/path/file.md"
            text = f"The user opened the file {fp} in the IDE."
            make_transcript([{
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": text}]},
            }], t)
            assert _context.get_ide_opened_file(str(t)) == fp


# --- T2.23-T2.28: find_project_from_file ---

class TestFindProjectFromFile(unittest.TestCase):

    def test_t2_23_valid_project_path(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            proj = cwd / "personal" / "projects" / "my-project"
            proj.mkdir(parents=True)
            result = _context.find_project_from_file(cwd, str(proj / "file.md"))
            assert result == [proj]

    def test_t2_24_path_not_relative_to_cwd(self):
        with tempfile.TemporaryDirectory() as d1:
            with tempfile.TemporaryDirectory() as d2:
                cwd = Path(d1)
                file_path = str(Path(d2) / "personal/projects/my-project/file.md")
                result = _context.find_project_from_file(cwd, file_path)
                assert result == []

    def test_t2_25_path_too_few_parts(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            result = _context.find_project_from_file(cwd, str(cwd / "file.md"))
            assert result == []

    def test_t2_26_invalid_context(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            result = _context.find_project_from_file(cwd, str(cwd / "other/projects/x/file.md"))
            assert result == []

    def test_t2_27_not_projects_dir(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            result = _context.find_project_from_file(cwd, str(cwd / "personal/areas/x/file.md"))
            assert result == []

    def test_t2_28_project_dir_does_not_exist(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            (cwd / "personal" / "projects").mkdir(parents=True)
            result = _context.find_project_from_file(cwd, str(cwd / "personal/projects/ghost/file.md"))
            assert result == []


# --- T2.29-T2.33: find_projects_in_message ---

class TestFindProjectsInMessage(unittest.TestCase):

    def _setup(self, d, name):
        cwd = Path(d)
        proj = cwd / "personal" / "projects" / name
        proj.mkdir(parents=True)
        return cwd, proj

    def test_t2_29_hyphen_form(self):
        with tempfile.TemporaryDirectory() as d:
            cwd, proj = self._setup(d, "my-project")
            result = _context.find_projects_in_message(cwd, "working on my-project today")
            assert proj in result

    def test_t2_30_space_form(self):
        with tempfile.TemporaryDirectory() as d:
            cwd, proj = self._setup(d, "my-project")
            result = _context.find_projects_in_message(cwd, "working on my project today")
            assert proj in result

    def test_t2_31_substring_match(self):
        with tempfile.TemporaryDirectory() as d:
            cwd, proj = self._setup(d, "my-project")
            result = _context.find_projects_in_message(cwd, "my-project-and-more")
            assert proj in result

    def test_t2_32_no_projects_dir_no_crash(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            result = _context.find_projects_in_message(cwd, "my-project")
            assert result == []

    def test_t2_33_no_match(self):
        with tempfile.TemporaryDirectory() as d:
            cwd, _ = self._setup(d, "my-project")
            result = _context.find_projects_in_message(cwd, "nothing relevant here")
            assert result == []


# --- T2.34-T2.41: inject-context-claude.py / inject-context-memory.py main() ---

class TestInjectContextMain(unittest.TestCase):

    def _vault(self, d, name, claude=None, memory=None):
        vault = Path(d)
        proj = vault / "personal" / "projects" / name
        proj.mkdir(parents=True)
        if claude is not None:
            (proj / "CLAUDE.md").write_text(claude, encoding="utf-8")
        if memory is not None:
            (proj / "_memory.md").write_text(memory, encoding="utf-8")
        return vault, proj

    def _t(self, d, text, second_turn=False):
        t = Path(d) / "t.jsonl"
        entries = [{"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}]
        if second_turn:
            entries.append({"type": "assistant", "message": {"role": "assistant"}})
        make_transcript(entries, t)
        return t

    def test_t2_34_claude_md_injected(self):
        with tempfile.TemporaryDirectory() as d:
            vault, _ = self._vault(d, "my-project", claude="# CLAUDE\nProject rules.")
            t = self._t(d, "my-project work")
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "my-project work"})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert "Project rules." in out

    def test_t2_35_memory_md_injected(self):
        with tempfile.TemporaryDirectory() as d:
            vault, _ = self._vault(d, "my-project", memory="# Memory\nCurrent state.")
            t = self._t(d, "my-project work")
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "my-project work"})
            rc, out = run_script("inject-context-memory.py", hook)
            assert rc == 0
            assert "Current state." in out

    def test_t2_36_multiple_projects_separated(self):
        with tempfile.TemporaryDirectory() as d:
            vault = Path(d)
            for name, content in [("proj-a", "# Alpha"), ("proj-b", "# Beta")]:
                p = vault / "personal" / "projects" / name
                p.mkdir(parents=True)
                (p / "CLAUDE.md").write_text(content, encoding="utf-8")
            t = self._t(d, "proj-a and proj-b")
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "proj-a and proj-b"})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert "# Alpha" in out
            assert "# Beta" in out
            assert "---" in out

    def test_t2_37_ide_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            vault, _ = self._vault(d, "my-project", claude="# Fallback project.")
            ide_path = str(vault / "personal/projects/my-project/notes.md")
            text = f"The user opened the file {ide_path} in the IDE. no project name in message"
            t = Path(d) / "t.jsonl"
            make_transcript([{
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": text}]},
            }], t)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": ""})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert "Fallback project." in out

    def test_t2_38_missing_claude_md_no_crash(self):
        with tempfile.TemporaryDirectory() as d:
            vault, _ = self._vault(d, "my-project")  # no CLAUDE.md
            t = self._t(d, "my-project work")
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "my-project work"})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert out.strip() == ""

    def test_t2_39_ide_fallback_not_in_project(self):
        with tempfile.TemporaryDirectory() as d:
            vault = Path(d)
            (vault / "personal" / "projects").mkdir(parents=True)
            ide_path = str(vault / "some/other/file.md")
            text = f"The user opened the file {ide_path} in the IDE."
            t = Path(d) / "t.jsonl"
            make_transcript([{
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": text}]},
            }], t)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": ""})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert out.strip() == ""

    def test_t2_40_message_and_ide_same_project_once(self):
        with tempfile.TemporaryDirectory() as d:
            vault, _ = self._vault(d, "my-project", claude="# MyProject")
            ide_path = str(vault / "personal/projects/my-project/file.md")
            text = f"project: my-project\nThe user opened the file {ide_path} in the IDE."
            t = Path(d) / "t.jsonl"
            make_transcript([{
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": text}]},
            }], t)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "my-project"})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert out.count("# MyProject") == 1

    def test_t2_41_second_turn_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            vault, _ = self._vault(d, "my-project", claude="# CLAUDE")
            t = self._t(d, "my-project work", second_turn=True)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "my-project work"})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert out.strip() == ""

    def test_t2_42_ide_selection_does_not_override_explicit_project(self):
        """IDE selection containing a different project's path must not inject that project
        when an explicit project name is already present in the typed message."""
        with tempfile.TemporaryDirectory() as d:
            vault = Path(d)
            for name, content in [("explicit-project", "# Explicit"), ("other-project", "# Other")]:
                p = vault / "personal" / "projects" / name
                p.mkdir(parents=True)
                (p / "CLAUDE.md").write_text(content, encoding="utf-8")
            ide_sel = (
                "<ide_selection>The user selected lines from "
                f"{vault}/personal/projects/other-project/file.md:\nsome content\n</ide_selection>"
            )
            prompt = f"{ide_sel}\n\nproject: explicit-project\ndo some work"
            t = self._t(d, prompt)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": prompt})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert "# Explicit" in out
            assert "# Other" not in out

    def test_t2_43_ide_selection_alone_does_not_inject(self):
        """An <ide_selection> block with a project path but no explicit project name
        and no 'opened file' annotation must not trigger any injection."""
        with tempfile.TemporaryDirectory() as d:
            vault, _ = self._vault(d, "my-project", claude="# MyProject")
            ide_sel = (
                "<ide_selection>The user selected lines from "
                f"{vault}/personal/projects/my-project/file.md:\nsome content\n</ide_selection>"
            )
            prompt = f"{ide_sel}\n\nno project name here"
            t = self._t(d, prompt)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": prompt})
            rc, out = run_script("inject-context-claude.py", hook)
            assert rc == 0
            assert out.strip() == ""


# --- T2.44: strip_ide_selection ---

class TestStripIdeSelection(unittest.TestCase):

    def test_t2_44_strips_ide_selection_block(self):
        msg = "<ide_selection>path/to/cv-update-job-search/file.md\ncontent\n</ide_selection>\nproject: home-lab"
        result = _context.strip_ide_selection(msg)
        assert "cv-update-job-search" not in result
        assert "project: home-lab" in result

    def test_t2_45_no_ide_selection_unchanged(self):
        msg = "project: home-lab\nsome question"
        assert _context.strip_ide_selection(msg) == msg

    def test_t2_46_multiple_ide_selection_blocks_stripped(self):
        msg = "<ide_selection>block1</ide_selection> text <ide_selection>block2</ide_selection> keep"
        result = _context.strip_ide_selection(msg)
        assert "block1" not in result
        assert "block2" not in result
        assert "keep" in result


# --- Smoke tests ---

class TestSmoke(unittest.TestCase):

    def test_smoke_self_imports_declared(self):
        """Root CLAUDE.md must import both _self/ files — they have no hook fallback."""
        claude_md = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
        assert "@_self/about.md" in claude_md
        assert "@_self/corrections.md" in claude_md

    def test_smoke_inject_context_claude(self):
        hook = json.dumps({"cwd": str(REPO), "prompt": "second-brain-setup"})
        rc, _ = run_script("inject-context-claude.py", hook)
        assert rc == 0

    def test_smoke_inject_context_memory(self):
        hook = json.dumps({"cwd": str(REPO), "prompt": "second-brain-setup"})
        rc, _ = run_script("inject-context-memory.py", hook)
        assert rc == 0


if __name__ == "__main__":
    unittest.main(verbosity=2)
