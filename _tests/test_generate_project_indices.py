#!/usr/bin/env python3
"""T9 — Tests for generate-project-indices.py (subfolder index generation)."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "_scripts"


def load_script(name):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_").replace(".", "_"), path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_idx = load_script("generate-project-indices.py")


def make_project(root, name, subdir=None, subdir_files=None):
    """Create a minimal project dir with index.md; optionally a subdir with files."""
    project = root / name
    project.mkdir(parents=True)
    (project / "index.md").write_text(f"# {name}\n", encoding="utf-8")
    if subdir and subdir_files:
        sub = project / subdir
        sub.mkdir()
        for fname, content in subdir_files.items():
            (sub / fname).write_text(content, encoding="utf-8")
    return project


# ── T9.1–T9.4  subfolder index generation ────────────────────────────────────

class TestSubfolderIndexGeneration(unittest.TestCase):

    def test_T9_1_subdir_with_md_files_gets_index(self):
        """Subdir with .md files and no index.md → index.md generated; subdir linked from parent."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = make_project(root, "my-project", "docs", {"note.md": "# Note\n"})
            _idx.update_index(project, project / "index.md", "my-project", [])
            assert (project / "docs" / "index.md").exists()
            parent_content = (project / "index.md").read_text(encoding="utf-8")
            assert "[[my-project/docs/index|docs]]" in parent_content

    def test_T9_2_existing_subdir_index_not_overwritten(self):
        """Subdir already has index.md → not overwritten; original content preserved."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = make_project(root, "my-project", "docs", {"note.md": "# Note\n"})
            existing = project / "docs" / "index.md"
            existing.write_text("# Custom Index\n\nManual content.\n", encoding="utf-8")
            _idx.update_index(project, project / "index.md", "my-project", [])
            assert "Custom Index" in existing.read_text(encoding="utf-8")

    def test_T9_3_underscore_subdir_skipped(self):
        """Subdir starting with _ → no index.md generated, not linked from parent."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = make_project(root, "my-project", "_internal", {"secret.md": "# S\n"})
            _idx.update_index(project, project / "index.md", "my-project", [])
            assert not (project / "_internal" / "index.md").exists()
            parent_content = (project / "index.md").read_text(encoding="utf-8")
            assert "_internal" not in parent_content

    def test_T9_4_empty_subdir_skipped(self):
        """Subdir with no .md files → no index.md generated."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = make_project(root, "my-project")
            empty_sub = project / "empty"
            empty_sub.mkdir()
            _idx.update_index(project, project / "index.md", "my-project", [])
            assert not (empty_sub / "index.md").exists()

    def test_T9_5_generated_stub_contains_backlink(self):
        """Generated subdir index.md contains backlink to project index."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = make_project(root, "my-project", "analysis", {"data.md": "# D\n"})
            _idx.update_index(project, project / "index.md", "my-project", [])
            stub = (project / "analysis" / "index.md").read_text(encoding="utf-8")
            assert "[[my-project/index" in stub


if __name__ == "__main__":
    unittest.main()
