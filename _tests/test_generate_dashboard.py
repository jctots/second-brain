#!/usr/bin/env python3
"""T5 — Tests for generate-dashboard.py"""
import importlib.util
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


_dash = load_script("generate-dashboard.py")


def run_script():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "generate-dashboard.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(REPO),
    )
    return result.returncode, result.stdout


def write_resource(path, tags=None, content="# Resource"):
    lines = []
    if tags is not None:
        tag_str = ", ".join(f'"{t}"' if " " in t else t for t in tags)
        lines += ["---", f"tags: [{tag_str}]", "---", ""]
    lines.append(content)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


# --- T5.1-T5.7: collect_resources ---

class TestCollectResources(unittest.TestCase):

    def test_t5_1_normal_md_file_included(self):
        with tempfile.TemporaryDirectory() as d:
            para = Path(d)
            write_resource(para / "my-note.md")
            result = [wl for wl, _ in _dash.collect_resources(para)]
            assert "[[my-note]]" in result

    def test_t5_2_subdir_with_index_md(self):
        with tempfile.TemporaryDirectory() as d:
            para = Path(d)
            (para / "my-topic").mkdir()
            (para / "my-topic/index.md").write_text("# Index", encoding="utf-8")
            result = [wl for wl, _ in _dash.collect_resources(para)]
            assert "[[my-topic/index|my-topic]]" in result

    def test_t5_3_subdir_without_index_individual_files(self):
        with tempfile.TemporaryDirectory() as d:
            para = Path(d)
            sub = para / "my-topic"
            sub.mkdir()
            (sub / "note-a.md").write_text("# A", encoding="utf-8")
            (sub / "note-b.md").write_text("# B", encoding="utf-8")
            result = [wl for wl, _ in _dash.collect_resources(para)]
            assert "[[my-topic/note-a]]" in result
            assert "[[my-topic/note-b]]" in result

    def test_t5_4_tags_dir_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            para = Path(d)
            tags_dir = para / "tags"
            tags_dir.mkdir()
            (tags_dir / "python.md").write_text("# python", encoding="utf-8")
            result = [wl for wl, _ in _dash.collect_resources(para)]
            assert not any("tags" in wl for wl in result)

    def test_t5_5_tags_dir_files_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            para = Path(d)
            tags_dir = para / "tags"
            tags_dir.mkdir()
            (tags_dir / "ai.md").write_text("# ai", encoding="utf-8")
            (tags_dir / "tools.md").write_text("# tools", encoding="utf-8")
            result = [wl for wl, _ in _dash.collect_resources(para)]
            assert result == []

    def test_t5_6_root_index_md_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            para = Path(d)
            (para / "index.md").write_text("# Index", encoding="utf-8")
            result = [wl for wl, _ in _dash.collect_resources(para)]
            assert "[[index]]" not in result

    def test_t5_7_non_md_file_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            para = Path(d)
            (para / "data.csv").write_text("a,b,c", encoding="utf-8")
            result = [wl for wl, _ in _dash.collect_resources(para)]
            assert result == []


# --- T5.8-T5.13: parse_snapshot ---

class TestParseSnapshot(unittest.TestCase):

    def _write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_t5_8_snapshot_text_extracted(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "_memory.md"
            self._write(m, "## Snapshot\n\nActive phase\n")
            status, nexts = _dash.parse_snapshot(m)
            assert status == "Active phase"
            assert nexts == []

    def test_t5_9_snapshot_trailing_whitespace_stripped(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "_memory.md"
            self._write(m, "## Snapshot\n\nActive phase   \n")
            status, _ = _dash.parse_snapshot(m)
            assert status == "Active phase"

    def test_t5_10_file_does_not_exist(self):
        status, nexts = _dash.parse_snapshot(Path("/nonexistent/_memory.md"))
        assert status is None
        assert nexts == []

    def test_t5_11_no_snapshot_section(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "_memory.md"
            self._write(m, "## Something else\n\nSome text\n")
            status, nexts = _dash.parse_snapshot(m)
            assert status is None
            assert nexts == []

    def test_t5_12_empty_snapshot_next_actions_still_parsed(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "_memory.md"
            self._write(m, "## Snapshot\n\n## Next Actions\n\n- Do thing\n")
            status, nexts = _dash.parse_snapshot(m)
            assert status is None
            assert nexts == ["Do thing"]

    def test_t5_13_stops_at_next_heading(self):
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "_memory.md"
            self._write(m, "## Snapshot\n\nOK\n\n## Other section\n\nshould not appear\n")
            status, nexts = _dash.parse_snapshot(m)
            assert status == "OK"
            assert nexts == []


# --- T5.14-T5.18: parse_frontmatter_tags ---

class TestParseFrontmatterTags(unittest.TestCase):

    def _write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_t5_14_tags_list(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "f.md"
            self._write(f, "---\ntags: [foo, bar]\n---\n")
            assert _dash.parse_frontmatter_tags(f) == ["foo", "bar"]

    def test_t5_15_hash_prefix_stripped(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "f.md"
            self._write(f, "---\ntags: [#foo, #bar]\n---\n")
            result = _dash.parse_frontmatter_tags(f)
            assert "foo" in result
            assert "bar" in result
            assert not any(t.startswith("#") for t in result)

    def test_t5_16_empty_tags(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "f.md"
            self._write(f, "---\ntags: []\n---\n")
            assert _dash.parse_frontmatter_tags(f) == []

    def test_t5_17_no_tags_key(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "f.md"
            self._write(f, "---\ntitle: hello\n---\n")
            assert _dash.parse_frontmatter_tags(f) == []

    def test_t5_18_quoted_tags(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "f.md"
            self._write(f, '---\ntags: ["foo", "bar"]\n---\n')
            result = _dash.parse_frontmatter_tags(f)
            assert result == ["foo", "bar"]


# --- T5.19-T5.21: generate_tag_pages ---

class TestGenerateTagPages(unittest.TestCase):

    def _setup(self, d, resources):
        """resources: list of (filename, tags_list)"""
        root = Path(d)
        res_dir = root / "personal" / "resources"
        res_dir.mkdir(parents=True)
        for fname, tags in resources:
            tag_str = ", ".join(f'"{t}"' for t in tags) if tags else ""
            content = f"---\ntags: [{tag_str}]\n---\n# Note\n"
            (res_dir / fname).write_text(content, encoding="utf-8")
        return root

    def test_t5_19_tag_pages_correct_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._setup(d, [("note-a.md", ["python"]), ("note-b.md", ["python", "tools"])])
            _dash.generate_tag_pages(root)
            tags_dir = root / "personal" / "resources" / "tags"
            python_page = tags_dir / "python.md"
            assert python_page.exists()
            text = python_page.read_text(encoding="utf-8")
            assert "context: personal" in text
            assert "para: resources" in text
            assert "tags: [python]" in text
            assert "created:" in text
            assert "[[dashboard" in text

    def test_t5_20_created_date_preserved_on_rerun(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._setup(d, [("note-a.md", ["python"])])
            # First run — creates tag page with today's date
            _dash.generate_tag_pages(root)
            tags_dir = root / "personal" / "resources" / "tags"
            python_page = tags_dir / "python.md"
            # Inject an old created date to simulate a previous run
            text = python_page.read_text(encoding="utf-8")
            old_date = "2025-01-01"
            text = text.replace("created:", f"created: {old_date}\ncreated_replaced:", 1)
            # Rewrite with old date
            import re as _re
            text = _re.sub(r"created:\s*\S+", f"created: {old_date}", text)
            python_page.write_text(text, encoding="utf-8")
            # Second run — should preserve the old date
            _dash.generate_tag_pages(root)
            text2 = (tags_dir / "python.md").read_text(encoding="utf-8")
            assert old_date in text2

    def test_t5_21_no_tagged_resources_no_crash(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._setup(d, [("note-a.md", [])])
            _dash.generate_tag_pages(root)
            tags_dir = root / "personal" / "resources" / "tags"
            assert not tags_dir.exists() or list(tags_dir.iterdir()) == []


# --- T5.23: parse_snapshot returns next items ---

class TestParseSnapshotNextItems(unittest.TestCase):

    def _write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_t5_23_next_actions_returned(self):
        """## Next Actions bullets → returned in nexts list; snapshot text also correct."""
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "_memory.md"
            self._write(m, "## Snapshot\n\nActive\n\n## Next Actions\n\n- Do A\n- Do B\n")
            status, nexts = _dash.parse_snapshot(m)
            assert status == "Active"
            assert nexts == ["Do A", "Do B"]


# --- T5.24-T5.27: generate_health_block ---

class TestGenerateHealthBlock(unittest.TestCase):

    def _make_root(self, tmp):
        root = Path(tmp)
        (root / "_conversations").mkdir()
        (root / "_self").mkdir()
        (root / "_inbox").mkdir()
        return root

    def _write_pending(self, root, lines):
        content = "<!-- AUTO-GENERATED -->\n\n# Pending Events\n\n" + "\n".join(lines) + "\n"
        (root / "_conversations" / "pending-events.md").write_text(content, encoding="utf-8")

    def test_t5_24_no_issues_ok_line(self):
        """No pending events, empty inbox, no oversized files, no rag-status → single OK line."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._make_root(tmp)
            result = _dash.generate_health_block(root)
        # Should contain the ok summary line (no issue lines)
        full = "\n".join(result)
        assert "📬 no pending events" in full
        assert "📦 inbox empty" in full
        assert "budget OK" in full

    def test_t5_25_pending_events_shown(self):
        """Pending events present → issue line with event type counts."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._make_root(tmp)
            self._write_pending(root, [
                "- [[conv-a]] — pending: memory, distill",
                "- [[conv-b]] — pending: memory",
            ])
            result = _dash.generate_health_block(root)
        full = "\n".join(result)
        assert "Pending events" in full
        assert "2 memory" in full
        assert "1 distill" in full
        assert "/maintain" in full

    def test_t5_26_inbox_items_shown(self):
        """Inbox has .md files → issue line with count."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._make_root(tmp)
            (root / "_inbox" / "capture.md").write_text("# note", encoding="utf-8")
            (root / "_inbox" / "another.md").write_text("# note2", encoding="utf-8")
            result = _dash.generate_health_block(root)
        full = "\n".join(result)
        assert "Inbox" in full
        assert "2 items" in full

    def test_t5_27_rag_error_shown(self):
        """rag-status file has error state → issue line with service detail."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._make_root(tmp)
            (root / ".rag-status").write_text(
                "error|2026-05-28 09:00|Ollama unreachable (host:11434)", encoding="utf-8"
            )
            result = _dash.generate_health_block(root)
        full = "\n".join(result)
        assert "RAG" in full
        assert "unavailable" in full
        assert "2026-05-28 09:00" in full


# --- Smoke test ---

class TestSmoke(unittest.TestCase):

    def test_t5_22_smoke_generate_dashboard(self):
        rc, _ = run_script()
        assert rc == 0
        assert (REPO / "dashboard.md").exists()


if __name__ == "__main__":
    unittest.main(verbosity=2)
