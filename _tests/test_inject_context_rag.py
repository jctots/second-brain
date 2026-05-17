#!/usr/bin/env python3
"""T8 — Tests for inject-context-rag.py."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from io import StringIO
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).parent.parent / "_scripts"


def load_script(name):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_").replace(".", "_"), path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_rag = load_script("inject-context-rag.py")

_FAKE_VEC = [0.1] * 768


class _Utf8Out(StringIO):
    """StringIO with encoding attribute so the script's stdout-reopen guard is a no-op."""
    encoding = "utf-8"


# ── T8.1–T8.4  extract_h1 ────────────────────────────────────────────────────

class TestExtractH1(unittest.TestCase):

    def test_T8_1_h1_after_frontmatter(self):
        """H1 after YAML frontmatter → returns heading text; frontmatter state machine works."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("---\ntitle: something\n---\n# My Title\n\nContent.")
            path = Path(f.name)
        try:
            self.assertEqual(_rag.extract_h1(path), "My Title")
        finally:
            path.unlink()

    def test_T8_2_h1_inside_frontmatter_not_returned(self):
        """H1-looking line inside frontmatter block → skipped; stem returned instead."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("---\n# Not A Title\ntitle: foo\n---\nNo heading after this.")
            path = Path(f.name)
        try:
            self.assertEqual(_rag.extract_h1(path), path.stem)
        finally:
            path.unlink()

    def test_T8_3_no_h1_within_30_lines_returns_stem(self):
        """No H1 in first 30 lines → early-exit guard triggers, stem returned."""
        lines = [f"Line {i}" for i in range(32)] + ["# Title Too Late"]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("\n".join(lines))
            path = Path(f.name)
        try:
            self.assertEqual(_rag.extract_h1(path), path.stem)
        finally:
            path.unlink()

    def test_T8_4_missing_file_returns_stem(self):
        """File does not exist → OSError caught silently, stem returned."""
        path = Path("/nonexistent/vault/missing-note.md")
        self.assertEqual(_rag.extract_h1(path), "missing-note")


# ── T8.5–T8.8  main() — graceful degradation ─────────────────────────────────

class TestMainDegradation(unittest.TestCase):

    def _run(self, hook_data, env):
        """Run _rag.main() with patched stdin/stdout/env; return (stdout, exit_code)."""
        out = _Utf8Out()
        exit_code = None
        try:
            with patch.dict(os.environ, env):
                with patch("sys.stdin", StringIO(json.dumps(hook_data))):
                    with patch("sys.stdout", out):
                        _rag.main()
        except SystemExit as e:
            exit_code = e.code
        return out.getvalue(), exit_code

    def test_T8_5_ollama_host_not_set_exits_0_no_output(self):
        """OLLAMA_HOST empty → exits 0, no output, ollama_embed never called."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(_rag, "ollama_embed") as mock_embed:
                out, code = self._run(
                    {"cwd": tmp, "prompt": "test query"},
                    {"OLLAMA_HOST": "", "QDRANT_HOST": "somehost"},
                )
            mock_embed.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_T8_6_qdrant_host_not_set_exits_0_no_output(self):
        """QDRANT_HOST empty → exits 0, no output, ollama_embed never called."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(_rag, "ollama_embed") as mock_embed:
                out, code = self._run(
                    {"cwd": tmp, "prompt": "test query"},
                    {"OLLAMA_HOST": "somehost", "QDRANT_HOST": ""},
                )
            mock_embed.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_T8_7_empty_prompt_exits_0_no_output(self):
        """Whitespace-only prompt → exits 0, no output."""
        with tempfile.TemporaryDirectory() as tmp:
            out, code = self._run(
                {"cwd": tmp, "prompt": "   "},
                {"OLLAMA_HOST": "somehost", "QDRANT_HOST": "somehost"},
            )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_T8_8_url_error_exits_0_no_output(self):
        """URLError from network call → exits 0, no output."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(_rag, "ollama_embed", side_effect=urllib.error.URLError("refused")):
                out, code = self._run(
                    {"cwd": tmp, "prompt": "test query"},
                    {"OLLAMA_HOST": "somehost", "QDRANT_HOST": "somehost"},
                )
        self.assertEqual(code, 0)
        self.assertEqual(out, "")


# ── T8.9–T8.12  main() — filtering and deduplication ─────────────────────────

class TestMainFiltering(unittest.TestCase):

    _ENV = {"OLLAMA_HOST": "somehost", "QDRANT_HOST": "somehost", "RAG_SCORE_THRESHOLD": "0.55"}

    def _run(self, tmp, results, prompt="query"):
        out = _Utf8Out()
        exit_code = None
        try:
            with patch.dict(os.environ, self._ENV):
                with patch("sys.stdin", StringIO(json.dumps({"cwd": str(tmp), "prompt": prompt}))):
                    with patch("sys.stdout", out):
                        with patch.object(_rag, "ollama_embed", return_value=_FAKE_VEC):
                            with patch.object(_rag, "qdrant_search", return_value=results):
                                _rag.main()
        except SystemExit as e:
            exit_code = e.code
        return out.getvalue(), exit_code

    def test_T8_9_empty_result_list_exits_0_no_output(self):
        """Qdrant returns [] → seen stays empty, exits 0, no output."""
        with tempfile.TemporaryDirectory() as tmp:
            out, code = self._run(tmp, [])
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_T8_10_all_below_threshold_exits_0_no_output(self):
        """All hit scores below SCORE_THRESHOLD (0.55) → exits 0, no output."""
        results = [
            {"payload": {"file_path": "personal/areas/a.md"}, "score": 0.40},
            {"payload": {"file_path": "personal/areas/b.md"}, "score": 0.30},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out, code = self._run(tmp, results)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_T8_11_deduplication_same_file_appears_once(self):
        """Same file_path in two hits (0.60 then 0.65) — score > seen[fp] branch exercised; file appears once."""
        results = [
            {"payload": {"file_path": "personal/areas/dup.md"}, "score": 0.60},
            {"payload": {"file_path": "personal/areas/dup.md"}, "score": 0.65},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            area = Path(tmp) / "personal" / "areas"
            area.mkdir(parents=True)
            (area / "dup.md").write_text("# Dup Note\n", encoding="utf-8")
            out, _ = self._run(tmp, results)
        entry_lines = [l for l in out.splitlines() if l.startswith("- ")]
        self.assertEqual(len(entry_lines), 1)

    def test_T8_12_max_files_limit_top_3_only(self):
        """Four results above threshold → only top 3 in output; lowest-score file excluded."""
        results = [
            {"payload": {"file_path": "personal/areas/a.md"}, "score": 0.90},
            {"payload": {"file_path": "personal/areas/b.md"}, "score": 0.80},
            {"payload": {"file_path": "personal/areas/c.md"}, "score": 0.70},
            {"payload": {"file_path": "personal/areas/d.md"}, "score": 0.60},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out, _ = self._run(tmp, results)
        self.assertIn("personal/areas/a.md", out)
        self.assertIn("personal/areas/b.md", out)
        self.assertIn("personal/areas/c.md", out)
        self.assertNotIn("personal/areas/d.md", out)


# ── T8.13  main() — output format ─────────────────────────────────────────────

class TestMainOutputFormat(unittest.TestCase):

    def test_T8_13_header_em_dash_and_score_ordering(self):
        """Results above threshold → correct header, em-dash separator, highest score first."""
        results = [
            {"payload": {"file_path": "personal/areas/alpha.md"}, "score": 0.70},
            {"payload": {"file_path": "personal/areas/beta.md"}, "score": 0.85},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            area = Path(tmp) / "personal" / "areas"
            area.mkdir(parents=True)
            (area / "alpha.md").write_text("# Alpha Note\n", encoding="utf-8")
            (area / "beta.md").write_text("# Beta Note\n", encoding="utf-8")

            out = _Utf8Out()
            with patch.dict(os.environ, {"OLLAMA_HOST": "somehost", "QDRANT_HOST": "somehost"}):
                with patch("sys.stdin", StringIO(json.dumps({"cwd": str(tmp), "prompt": "query"}))):
                    with patch("sys.stdout", out):
                        with patch.object(_rag, "ollama_embed", return_value=_FAKE_VEC):
                            with patch.object(_rag, "qdrant_search", return_value=results):
                                _rag.main()

        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0], "## Relevant vault notes")
        self.assertIn("personal/areas/beta.md — Beta Note", lines[1])
        self.assertIn("personal/areas/alpha.md — Alpha Note", lines[2])
        self.assertIn(" — ", lines[1])


if __name__ == "__main__":
    unittest.main()
