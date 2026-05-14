#!/usr/bin/env python3
"""T6 — Tests for rag-embed.py"""
import importlib.util
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


_embed = load_script("rag-embed.py")

make_point_id = _embed.make_point_id
should_skip = _embed.should_skip
split_sections = _embed.split_sections
chunk_section = _embed.chunk_section
MAX_CHARS = _embed.MAX_CHARS
OVERLAP_CHARS = _embed.OVERLAP_CHARS


# ── T6.22–T6.25  make_point_id ────────────────────────────────────────────────

class TestMakePointId(unittest.TestCase):

    def test_T6_22_deterministic(self):
        """Same inputs always produce the same ID."""
        a = make_point_id("personal/projects/foo/bar.md", "Introduction", 0)
        b = make_point_id("personal/projects/foo/bar.md", "Introduction", 0)
        self.assertEqual(a, b)

    def test_T6_23_different_file_paths(self):
        """Different file paths produce different IDs even with same heading and idx."""
        a = make_point_id("personal/projects/foo/bar.md", "Intro", 0)
        b = make_point_id("personal/projects/foo/baz.md", "Intro", 0)
        self.assertNotEqual(a, b)

    def test_T6_24_different_idx(self):
        """Different idx for the same file and heading produces different IDs."""
        a = make_point_id("personal/projects/foo/bar.md", "Intro", 0)
        b = make_point_id("personal/projects/foo/bar.md", "Intro", 1)
        self.assertNotEqual(a, b)

    def test_T6_25_uuid_format(self):
        """Output matches UUID format: 8-4-4-4-12 lowercase hex."""
        uid = make_point_id("some/file.md", "heading", 0)
        parts = uid.split("-")
        self.assertEqual(len(parts), 5)
        self.assertEqual([len(p) for p in parts], [8, 4, 4, 4, 12])
        self.assertTrue(all(c in "0123456789abcdef" for p in parts for c in p))


# ── T6.26–T6.29  should_skip ──────────────────────────────────────────────────

class TestShouldSkip(unittest.TestCase):

    def _rel(self, *parts):
        return Path(*parts)

    def test_T6_26_skip_dir_conversations(self):
        """Files inside a SKIP_DIR are skipped."""
        self.assertTrue(should_skip(self._rel("_conversations", "note.md")))

    def test_T6_27_skip_file_index(self):
        """Files named index.md are skipped regardless of location."""
        self.assertTrue(should_skip(self._rel("personal", "projects", "foo", "index.md")))

    def test_T6_28_skip_file_dashboard(self):
        """dashboard.md is skipped — it is a generated file."""
        self.assertTrue(should_skip(self._rel("dashboard.md")))

    def test_T6_29_valid_content_path(self):
        """A normal content note is not skipped."""
        self.assertFalse(should_skip(self._rel("personal", "areas", "health", "note.md")))


# ── T6.13–T6.21  split_sections + chunk_section ───────────────────────────────

class TestSplitSections(unittest.TestCase):

    def test_T6_13_two_headings(self):
        """Body with two ## headings returns preamble + two sections."""
        body = "intro text\n\n## First\n\ncontent one\n\n## Second\n\ncontent two"
        sections = split_sections(body)
        headings = [h for h, _ in sections]
        self.assertIn("__preamble__", headings)
        self.assertIn("First", headings)
        self.assertIn("Second", headings)

    def test_T6_14_no_headings(self):
        """Body with no headings returns a single preamble entry."""
        body = "just some text with no headings"
        sections = split_sections(body)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0][0], "__preamble__")

    def test_T6_15_no_preamble(self):
        """Body starting immediately with a heading has no preamble entry."""
        body = "## First\n\ncontent"
        sections = split_sections(body)
        headings = [h for h, _ in sections]
        self.assertNotIn("__preamble__", headings)

    def test_T6_16_h1_not_matched(self):
        """A single # heading is not treated as a section boundary."""
        body = "# Title\n\nsome content"
        sections = split_sections(body)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0][0], "__preamble__")

    def test_T6_17_h3_matched(self):
        """A ### heading is matched (pattern covers h2 and h3)."""
        body = "### Deep heading\n\ncontent"
        sections = split_sections(body)
        headings = [h for h, _ in sections]
        self.assertIn("Deep heading", headings)


class TestChunkSection(unittest.TestCase):

    def test_T6_18_fits_in_one_chunk(self):
        """Short body returns a single chunk with idx 0."""
        body = "short content"
        chunks = chunk_section("My Section", body)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0][1], 0)

    def test_T6_19_multiple_chunks_with_overlap(self):
        """Long body produces multiple chunks advancing by MAX_CHARS - OVERLAP_CHARS."""
        body = "x" * (MAX_CHARS * 2)
        chunks = chunk_section("Long", body)
        self.assertGreater(len(chunks), 1)
        step = MAX_CHARS - OVERLAP_CHARS
        text0, _ = chunks[0]
        text1, _ = chunks[1]
        # Overlap: end of chunk 0 should equal start of chunk 1 (up to MAX_CHARS boundary)
        self.assertEqual(text0[step:], text1[:MAX_CHARS - step])

    def test_T6_20_preamble_has_no_prefix(self):
        """__preamble__ heading produces no ## prefix in chunk text."""
        chunks = chunk_section("__preamble__", "some body text")
        self.assertFalse(chunks[0][0].startswith("##"))

    def test_T6_21_normal_heading_has_prefix(self):
        """Normal heading is prepended as ## {heading}\\n\\n in chunk text."""
        chunks = chunk_section("Introduction", "body text")
        self.assertTrue(chunks[0][0].startswith("## Introduction\n\n"))


if __name__ == "__main__":
    unittest.main()
