#!/usr/bin/env python3
"""T10 — Tests for inject-context-projects.py"""
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


_projects = load_script("inject-context-projects.py")


def run_script(stdin_data):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "inject-context-projects.py")],
        input=stdin_data,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.returncode, result.stdout


def make_transcript(entries, path):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


# --- T10.1–T10.3: extract_snapshot ---

class TestExtractSnapshot(unittest.TestCase):

    def test_t10_1_snapshot_section_with_text(self):
        """## Snapshot section with a non-empty line → returns that line."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Memory\n\n## Snapshot\n\nActive project with open goals.\n\n## Next Actions\n")
            path = Path(f.name)
        try:
            assert _projects.extract_snapshot(path) == "Active project with open goals."
        finally:
            path.unlink()

    def test_t10_2_no_snapshot_section(self):
        """No ## Snapshot heading → returns None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# Memory\n\n## Current Status\nSome status.\n")
            path = Path(f.name)
        try:
            assert _projects.extract_snapshot(path) is None
        finally:
            path.unlink()

    def test_t10_3_missing_file(self):
        """File does not exist → returns None, no crash."""
        path = Path("/nonexistent/vault/missing-memory.md")
        assert _projects.extract_snapshot(path) is None

    def test_t10_4_snapshot_empty_next_section_follows(self):
        """## Snapshot present but no text before next ## heading → returns None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("## Snapshot\n\n## Next Actions\n- do something\n")
            path = Path(f.name)
        try:
            assert _projects.extract_snapshot(path) is None
        finally:
            path.unlink()


# --- T10.5–T10.8: collect_projects ---

class TestCollectProjects(unittest.TestCase):

    def test_t10_5_project_with_snapshot(self):
        """Project with _memory.md containing ## Snapshot → entry includes snapshot text."""
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            proj = cwd / "personal" / "projects" / "my-project"
            proj.mkdir(parents=True)
            (proj / "_memory.md").write_text("## Snapshot\n\nProject snapshot line.\n", encoding="utf-8")
            result = _projects.collect_projects(cwd)
        assert len(result) == 1
        path, snapshot = result[0]
        assert path == "personal/projects/my-project"
        assert snapshot == "Project snapshot line."

    def test_t10_6_project_without_memory_md(self):
        """Project with no _memory.md → listed with snapshot=None."""
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            proj = cwd / "personal" / "projects" / "bare-project"
            proj.mkdir(parents=True)
            result = _projects.collect_projects(cwd)
        assert len(result) == 1
        path, snapshot = result[0]
        assert path == "personal/projects/bare-project"
        assert snapshot is None

    def test_t10_7_multiple_contexts(self):
        """Projects in personal/ and professional/ → both appear in output, sorted by context."""
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            (cwd / "personal" / "projects" / "proj-a").mkdir(parents=True)
            (cwd / "professional" / "projects" / "proj-b").mkdir(parents=True)
            result = _projects.collect_projects(cwd)
        paths = [r[0] for r in result]
        assert "personal/projects/proj-a" in paths
        assert "professional/projects/proj-b" in paths
        assert paths.index("personal/projects/proj-a") < paths.index("professional/projects/proj-b")

    def test_t10_8_no_projects_dir(self):
        """No projects/ directory in any context → returns empty list, no crash."""
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            result = _projects.collect_projects(cwd)
        assert result == []

    def test_t10_9_hidden_dirs_skipped(self):
        """Directories starting with '.' → not included in results."""
        with tempfile.TemporaryDirectory() as d:
            cwd = Path(d)
            (cwd / "personal" / "projects" / ".hidden-dir").mkdir(parents=True)
            (cwd / "personal" / "projects" / "visible-project").mkdir(parents=True)
            result = _projects.collect_projects(cwd)
        paths = [r[0] for r in result]
        assert "personal/projects/visible-project" in paths
        assert not any(".hidden" in p for p in paths)


# --- T10.10–T10.15: main() ---

class TestMain(unittest.TestCase):

    def _vault(self, d, projects=None):
        """Create a temp vault with specified projects. projects = {context/projects/name: snapshot_or_None}."""
        cwd = Path(d)
        if projects:
            for rel, snapshot in projects.items():
                parts = rel.split("/")
                proj_dir = cwd / parts[0] / parts[1] / parts[2]
                proj_dir.mkdir(parents=True, exist_ok=True)
                if snapshot is not None:
                    (proj_dir / "_memory.md").write_text(
                        f"## Snapshot\n\n{snapshot}\n", encoding="utf-8"
                    )
        return cwd

    def _t(self, d, second_turn=False):
        t = Path(d) / "t.jsonl"
        entries = [{"type": "user"}]
        if second_turn:
            entries.append({"type": "assistant"})
        make_transcript(entries, t)
        return t

    def test_t10_10_first_turn_outputs_header(self):
        """First turn with projects → output starts with ## Active Projects."""
        with tempfile.TemporaryDirectory() as d:
            vault = self._vault(d, {"personal/projects/proj-a": "Snapshot A."})
            t = self._t(d)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "hello"})
            rc, out = run_script(hook)
        assert rc == 0
        assert out.startswith("## Active Projects")

    def test_t10_11_second_turn_no_output(self):
        """Second turn (assistant entry in transcript) → exits 0, no output."""
        with tempfile.TemporaryDirectory() as d:
            vault = self._vault(d, {"personal/projects/proj-a": "Snapshot A."})
            t = self._t(d, second_turn=True)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "hello"})
            rc, out = run_script(hook)
        assert rc == 0
        assert out.strip() == ""

    def test_t10_12_project_with_snapshot_uses_em_dash(self):
        """Project with snapshot → em dash separator between path and snapshot."""
        with tempfile.TemporaryDirectory() as d:
            vault = self._vault(d, {"personal/projects/my-proj": "My snapshot text."})
            t = self._t(d)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "hello"})
            rc, out = run_script(hook)
        assert rc == 0
        assert "personal/projects/my-proj — My snapshot text." in out

    def test_t10_13_project_without_snapshot_path_only(self):
        """Project with no _memory.md → listed as path only, no em dash."""
        with tempfile.TemporaryDirectory() as d:
            vault = self._vault(d, {"personal/projects/bare-proj": None})
            t = self._t(d)
            hook = json.dumps({"transcript_path": str(t), "cwd": str(vault), "prompt": "hello"})
            rc, out = run_script(hook)
        assert rc == 0
        lines = [l for l in out.splitlines() if l.startswith("- ")]
        assert any(l == "- personal/projects/bare-proj" for l in lines)

    def test_t10_14_empty_stdin_exits_0(self):
        """Empty stdin → exits 0, no output."""
        rc, out = run_script("")
        assert rc == 0
        assert out == ""

    def test_t10_15_no_projects_no_output(self):
        """No project directories in vault → exits 0, no output."""
        with tempfile.TemporaryDirectory() as d:
            hook = json.dumps({"cwd": d, "prompt": "hello"})
            rc, out = run_script(hook)
        assert rc == 0
        assert out.strip() == ""


# --- Smoke test ---

class TestSmoke(unittest.TestCase):

    def test_smoke_inject_context_projects(self):
        """Smoke: runs against real vault, exits 0, output contains ## Active Projects."""
        hook = json.dumps({"cwd": str(REPO), "prompt": "hello"})
        rc, out = run_script(hook)
        assert rc == 0
        assert "## Active Projects" in out


if __name__ == "__main__":
    unittest.main(verbosity=2)
