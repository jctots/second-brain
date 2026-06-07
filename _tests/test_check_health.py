#!/usr/bin/env python3
"""T11 — Tests for check-health.py (UserPromptSubmit hook — service reachability)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent.parent / "_scripts"

# Env with all service vars cleared — no services configured.
_EMPTY_ENV = {
    k: v for k, v in os.environ.items()
    if k not in ("OLLAMA_HOST", "QDRANT_HOST", "VIKUNJA_URL", "VIKUNJA_TOKEN",
                 "GITEA_URL", "GITEA_TOKEN", "NTFY_URL")
}
_EMPTY_ENV.update({
    "OLLAMA_HOST": "", "QDRANT_HOST": "",
    "VIKUNJA_URL": "", "VIKUNJA_TOKEN": "",
    "GITEA_URL": "", "GITEA_TOKEN": "",
    "NTFY_URL": "",
})


def run_health(stdin_data: str, extra_env: dict | None = None) -> tuple[int, str]:
    env = {**_EMPTY_ENV, **(extra_env or {})}
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "check-health.py")],
        input=stdin_data,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return result.returncode, result.stdout


def make_transcript(entries, path):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


# T11.1–T11.3: basic gate behaviour

class TestCheckHealthGate(unittest.TestCase):

    def test_t11_1_empty_stdin(self):
        rc, out = run_health("")
        assert rc == 0
        assert out == ""

    def test_t11_2_invalid_json_stdin(self):
        rc, out = run_health("not json")
        assert rc == 0
        assert out == ""

    def test_t11_3_second_turn_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript([{"type": "user"}, {"type": "assistant"}], t)
            hook = json.dumps({"transcript_path": str(t), "cwd": d, "prompt": "hello"})
            rc, out = run_health(hook)
            assert rc == 0
            assert out.strip() == ""


# T11.4: no services configured → silent

class TestCheckHealthNoServices(unittest.TestCase):

    def test_t11_4_no_services_silent(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t.jsonl"
            make_transcript([{"type": "user"}], t)
            hook = json.dumps({"transcript_path": str(t), "cwd": d, "prompt": "hello"})
            rc, out = run_health(hook)
            assert rc == 0
            assert out.strip() == ""


# T11.5–T11.8: service unreachable → warning printed
# Uses 127.0.0.1:19999 (closed port) with RAG_TIMEOUT=1 for fast failure.

_UNREACHABLE = "http://127.0.0.1:19999"
_FAST = {"RAG_TIMEOUT": "1"}


class TestCheckHealthServiceDown(unittest.TestCase):

    def _first_turn_hook(self, d):
        t = Path(d) / "t.jsonl"
        make_transcript([{"type": "user"}], t)
        return json.dumps({"transcript_path": str(t), "cwd": d, "prompt": "hello"})

    def test_t11_5_vikunja_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            hook = self._first_turn_hook(d)
            rc, out = run_health(hook, {**_FAST, "VIKUNJA_URL": _UNREACHABLE, "VIKUNJA_TOKEN": "fake"})
            assert rc == 0
            assert "⚠️ Service check:" in out
            assert "Vikunja unreachable" in out

    def test_t11_6_gitea_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            hook = self._first_turn_hook(d)
            rc, out = run_health(hook, {**_FAST, "GITEA_URL": _UNREACHABLE, "GITEA_TOKEN": "fake"})
            assert rc == 0
            assert "⚠️ Service check:" in out
            assert "Gitea unreachable" in out

    def test_t11_7_ntfy_unreachable(self):
        with tempfile.TemporaryDirectory() as d:
            hook = self._first_turn_hook(d)
            rc, out = run_health(hook, {**_FAST, "NTFY_URL": _UNREACHABLE})
            assert rc == 0
            assert "⚠️ Service check:" in out
            assert "ntfy unreachable" in out

    def test_t11_8_multiple_services_down_all_named(self):
        with tempfile.TemporaryDirectory() as d:
            hook = self._first_turn_hook(d)
            rc, out = run_health(hook, {
                **_FAST,
                "VIKUNJA_URL": _UNREACHABLE, "VIKUNJA_TOKEN": "fake",
                "GITEA_URL": _UNREACHABLE, "GITEA_TOKEN": "fake",
            })
            assert rc == 0
            assert "Vikunja unreachable" in out
            assert "Gitea unreachable" in out


if __name__ == "__main__":
    unittest.main(verbosity=2)
