#!/usr/bin/env python3
"""T4 — Tests for generate-pending-events.py"""
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


_pe = load_script("generate-pending-events.py")


def run_script():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "generate-pending-events.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(REPO),
    )
    return result.returncode, result.stdout


def write_conv(path, events=None, processed=None, extra_frontmatter=""):
    lines = ["---"]
    if events is not None:
        lines.append(f"events: {json.dumps(events)}")
    if processed is not None:
        lines.append(f"processed: {json.dumps(processed)}")
    if extra_frontmatter:
        lines.append(extra_frontmatter)
    lines += ["---", "", "# Body", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# --- T4.1-T4.8: parse_frontmatter ---

class TestParseFrontmatter(unittest.TestCase):

    def test_t4_1_valid_events_and_processed(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "2026-01-01-test.md"
            write_conv(f, events=["memory", "distill"], processed=["memory"])
            fm = _pe.parse_frontmatter(f)
            assert fm["events"] == ["memory", "distill"]
            assert fm["processed"] == ["memory"]

    def test_t4_2_only_events(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "2026-01-01-test.md"
            write_conv(f, events=["profile"])
            fm = _pe.parse_frontmatter(f)
            assert fm["events"] == ["profile"]
            assert fm["processed"] == []

    def test_t4_3_utf8_bom(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "2026-01-01-test.md"
            content = '---\nevents: ["memory"]\n---\n'
            f.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
            fm = _pe.parse_frontmatter(f)
            assert fm["events"] == ["memory"]

    def test_t4_4_no_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "2026-01-01-test.md"
            f.write_text("# Just a heading\nNo frontmatter.", encoding="utf-8")
            fm = _pe.parse_frontmatter(f)
            assert fm["events"] == []
            assert fm["processed"] == []

    def test_t4_5_unclosed_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "2026-01-01-test.md"
            f.write_text("---\nevents: [\"memory\"]\n# no closing dashes\n", encoding="utf-8")
            fm = _pe.parse_frontmatter(f)
            assert isinstance(fm["events"], list)  # no crash

    def test_t4_6_malformed_events(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "2026-01-01-test.md"
            f.write_text("---\nevents: [memory\n---\n", encoding="utf-8")
            fm = _pe.parse_frontmatter(f)
            assert fm["events"] == []

    def test_t4_7_malformed_processed(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "2026-01-01-test.md"
            f.write_text("---\nprocessed: [memory\n---\n", encoding="utf-8")
            fm = _pe.parse_frontmatter(f)
            assert fm["processed"] == []

    def test_t4_8_neither_key(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "2026-01-01-test.md"
            f.write_text("---\ntitle: hello\n---\n", encoding="utf-8")
            fm = _pe.parse_frontmatter(f)
            assert fm["events"] == []
            assert fm["processed"] == []


# --- T4.9-T4.17: main() ---

def run_in_dir(tmp_root):
    """Run generate-pending-events.py with REPO patched to tmp_root."""
    script = SCRIPTS / "generate-pending-events.py"
    src = script.read_text(encoding="utf-8")
    patched = src.replace(
        "root = Path(__file__).parent.parent",
        f"root = Path({repr(str(tmp_root))})",
    )
    patched_path = Path(tmp_root) / "_gen_pending_events_test.py"
    patched_path.write_text(patched, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(patched_path)],
        capture_output=True, text=True, encoding="utf-8",
    )
    patched_path.unlink(missing_ok=True)
    return result.returncode, result.stdout


def setup_root(d):
    root = Path(d)
    (root / "_conversations" / "2026" / "01").mkdir(parents=True)
    (root / "_conversations" / "pending-events.md").write_text("", encoding="utf-8")
    return root


class TestPendingEventsMain(unittest.TestCase):

    def test_t4_9_memory_event_no_processed(self):
        with tempfile.TemporaryDirectory() as d:
            root = setup_root(d)
            f = root / "_conversations/2026/01/2026-01-10-session.md"
            write_conv(f, events=["memory"])
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            assert "2026-01-10" in out
            assert "memory" in out

    def test_t4_10_event_fully_processed_not_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root = setup_root(d)
            f = root / "_conversations/2026/01/2026-01-10-session.md"
            write_conv(f, events=["memory"], processed=["memory"])
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            assert "2026-01-10" not in out

    def test_t4_11_partial_processed(self):
        with tempfile.TemporaryDirectory() as d:
            root = setup_root(d)
            f = root / "_conversations/2026/01/2026-01-10-session.md"
            write_conv(f, events=["memory", "distill"], processed=["memory"])
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            assert "distill" in out
            assert "memory" not in out.split("pending:")[-1] if "pending:" in out else True

    def test_t4_12_no_events_not_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root = setup_root(d)
            f = root / "_conversations/2026/01/2026-01-10-session.md"
            f.write_text("---\ntitle: nothing\n---\n", encoding="utf-8")
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            assert "No pending" in out

    def test_t4_13_sorted_newest_first(self):
        with tempfile.TemporaryDirectory() as d:
            root = setup_root(d)
            for date in ["2026-01-05", "2026-01-15", "2026-01-10"]:
                f = root / f"_conversations/2026/01/{date}-session.md"
                write_conv(f, events=["memory"])
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            idx_15 = out.find("2026-01-15")
            idx_10 = out.find("2026-01-10")
            idx_05 = out.find("2026-01-05")
            assert idx_15 < idx_10 < idx_05

    def test_t4_14_short_stem_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root = setup_root(d)
            f = root / "_conversations/notes.md"
            write_conv(f, events=["memory"])
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            assert "No pending" in out

    def test_t4_15_empty_conversations_no_crash(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "_conversations").mkdir()
            (root / "_conversations/pending-events.md").write_text("", encoding="utf-8")
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            assert "No pending" in out

    def test_t4_16_index_md_excluded(self):
        with tempfile.TemporaryDirectory() as d:
            root = setup_root(d)
            f = root / "_conversations/index.md"
            write_conv(f, events=["memory"])
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            assert "No pending" in out

    def test_t4_17_pending_events_md_not_self_referenced(self):
        with tempfile.TemporaryDirectory() as d:
            root = setup_root(d)
            write_conv(root / "_conversations/pending-events.md", events=["memory"])
            rc, _ = run_in_dir(root)
            assert rc == 0
            out = (root / "_conversations/pending-events.md").read_text(encoding="utf-8")
            assert "[[_conversations/pending-events]]" not in out


# --- Smoke test ---

class TestSmoke(unittest.TestCase):

    def test_smoke_generate_pending_events(self):
        rc, _ = run_script()
        assert rc == 0
        assert (REPO / "_conversations" / "pending-events.md").exists()


if __name__ == "__main__":
    unittest.main(verbosity=2)
