#!/usr/bin/env python3
"""T7 — Tests for rag-search.py degradation behavior."""
import importlib.util
import os
import sys
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


_search = load_script("rag-search.py")

_FAKE_VEC = [0.1] * 768
_FAKE_RESULTS = [
    {
        "score": 0.9,
        "payload": {
            "file_path": "personal/areas/test.md",
            "heading": "Section",
            "snippet": "Some content here",
        },
    }
]


# ── T7.1–T7.5  main() — graceful degradation ─────────────────────────────────

class TestSearchDegradation(unittest.TestCase):

    def _run_main(self, env, argv=None):
        """Run _search.main() with patched env and argv; return captured stdout."""
        out = StringIO()
        with patch.dict(os.environ, env):
            with patch("sys.argv", argv or ["rag-search.py", "test query"]):
                with patch("sys.stdout", out):
                    _search.main()
        return out.getvalue()

    def test_T7_1_not_configured_ollama_host_empty(self):
        """Empty OLLAMA_HOST → 'not configured' message, ollama_embed never called."""
        with patch.object(_search, "ollama_embed") as mock_embed:
            out = self._run_main({"OLLAMA_HOST": "", "QDRANT_HOST": "somehost"})
            mock_embed.assert_not_called()
            self.assertIn("not configured", out)

    def test_T7_2_not_configured_qdrant_host_empty(self):
        """Empty QDRANT_HOST → 'not configured' message, ollama_embed never called."""
        with patch.object(_search, "ollama_embed") as mock_embed:
            out = self._run_main({"OLLAMA_HOST": "somehost", "QDRANT_HOST": ""})
            mock_embed.assert_not_called()
            self.assertIn("not configured", out)

    def test_T7_3_ollama_unreachable_message_exits_0(self):
        """URLError from ollama_embed → 'Ollama unreachable' message, returns cleanly."""
        with patch.object(_search, "ollama_embed", side_effect=urllib.error.URLError("refused")):
            out = self._run_main({"OLLAMA_HOST": "somehost", "QDRANT_HOST": "somehost"})
            self.assertIn("Ollama unreachable", out)

    def test_T7_4_qdrant_unreachable_message_exits_0(self):
        """URLError from qdrant_search → 'Qdrant unreachable' message, returns cleanly."""
        with patch.object(_search, "ollama_embed", return_value=_FAKE_VEC):
            with patch.object(_search, "qdrant_search", side_effect=urllib.error.URLError("refused")):
                out = self._run_main({"OLLAMA_HOST": "somehost", "QDRANT_HOST": "somehost"})
                self.assertIn("Qdrant unreachable", out)

    def test_T7_5_configured_and_up_returns_results(self):
        """Configured and both services up → results printed to stdout."""
        with patch.object(_search, "ollama_embed", return_value=_FAKE_VEC):
            with patch.object(_search, "qdrant_search", return_value=_FAKE_RESULTS):
                out = self._run_main({"OLLAMA_HOST": "somehost", "QDRANT_HOST": "somehost"})
                self.assertIn("personal/areas/test.md", out)


if __name__ == "__main__":
    unittest.main()
