# Verification — Scripts and Hooks

Scenarios are identified as **T#.#** — first number is the test file, second is the case within it. IDs are unique across this document.

## Test file index

| T# | File | Covers |
|---|---|---|
| T1 | `test_hook_budget.py` | Hook injection budget enforcement |
| T2 | `test_inject_hooks.py` | `inject-profile.py`, `inject-corrections.py`, `inject-context-claude.py`, `inject-context-memory.py` |
| T3 | `test_save_conversation.py` | `save-conversation.py` |
| T4 | `test_generate_pending_events.py` | `generate-pending-events.py` |
| T5 | `test_generate_dashboard.py` | `generate-dashboard.py` |
| T6 | `test_rag_embed.py` | `rag-embed.py` — point ID stability, skip logic, chunking contracts, graceful degradation |
| T7 | `test_rag_search.py` | `rag-search.py` — graceful degradation (not configured, services down, happy path) |
| T8 | `test_inject_context_rag.py` | `inject-context-rag.py` — H1 extraction (frontmatter state machine, stem fallback), graceful degradation, threshold filtering, deduplication, output format |

Fixtures are created in `tempfile.TemporaryDirectory` per test and cleaned up after. Smoke tests run against the real vault (Gitea CI — full content available).

---

## T1 — `test_hook_budget.py`

This is a health check script, not a unit test file. It runs against the real vault — no isolated fixtures. When CI executes it, it reads the actual `_self/about.md`, `_self/corrections.md`, and each active project's `CLAUDE.md` and `_memory.md`, and fails if any exceed 10,000 chars.

### `main()` — real vault health check

| # | Scenario | Expected | Req |
|---|---|---|---|
| T1.1 | `_self/about.md` exists and within limit | Checked and reported as `OK` | R6 |
| T1.2 | `_self/corrections.md` exists and within limit | Checked and reported as `OK` | R6 |
| T1.3 | `_self/about.md` is missing | Reported as `FAIL`, added to failures, exit 1 | R6, R11 |
| T1.4 | `_self/corrections.md` is missing | Reported as `FAIL`, added to failures, exit 1 | R6, R11 |
| T1.5 | Project `CLAUDE.md` exists and within limit | Checked and reported as `OK` | R6 |
| T1.6 | Project `_memory.md` exists and within limit | Checked and reported as `OK` | R6 |
| T1.7 | Project filter arg provided (e.g. `personal/projects/my-project`) | Only matching project checked, others skipped | R6 |
| T1.8 | No projects exist in any context | Only `_self/` files checked, no crash | R6, R11 |

---

## T2 — `test_inject_hooks.py`

### `is_first_turn(transcript_path)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T2.1 | Transcript file does not exist | Returns `True` — treat as first turn | R11 |
| T2.2 | Transcript file exists, contains only user entries | Returns `True` | |
| T2.3 | Transcript file exists, contains at least one assistant entry | Returns `False` | |
| T2.4 | Transcript file exists but is empty | Returns `True` | R11 |
| T2.5 | Transcript file has lines with malformed JSON | Skips bad lines, continues scanning | R11 |
| T2.6 | Transcript file has blank lines interspersed | Skips blank lines, continues scanning | R11 |

### `inject-profile.py` / `inject-corrections.py` — `main()`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T2.7 | `_self/about.md` exists, first turn | Outputs content with correct label prefix, exits 0 | R6 |
| T2.8 | `_self/corrections.md` exists, first turn | Outputs content with correct label prefix, exits 0 | R6 |
| T2.9 | stdin is empty string | Exits 0, no output | R11 |
| T2.10 | stdin is invalid JSON | Exits 0, no output | R11 |
| T2.11 | Hook data has no `transcript_path` key | Injects unconditionally (no turn check), exits 0 | R11 |
| T2.12 | `transcript_path` present, second turn (assistant entry exists) | Exits 0, no output | |
| T2.13 | `_self/about.md` does not exist | Exits 0, no output — no crash | R11 |
| T2.14 | `cwd` missing from hook data | Defaults to `.`, no crash | R11 |

### `get_first_user_message(transcript_path)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T2.15 | Transcript has user entry with dict message and text block | Returns text content | |
| T2.16 | Transcript has user entry with string message | Returns the string | |
| T2.17 | Transcript does not exist | Returns `None` | R11 |
| T2.18 | Transcript has no user entries | Returns `None` | R11 |
| T2.19 | Transcript has malformed JSON lines | Skips bad lines, continues | R11 |

### `get_ide_opened_file(transcript_path)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T2.20 | Transcript has `<ide_opened_file>` annotation | Returns extracted file path | |
| T2.21 | No IDE annotation in any user entry | Returns `None` | R11 |
| T2.22 | Annotation present but path is an unusual absolute path | Returns path unchanged | R11 |

### `find_project_from_file(cwd, file_path)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T2.23 | File path is `{cwd}/personal/projects/my-project/file.md` | Returns `[my-project dir]` | |
| T2.24 | File path is not relative to `cwd` (different drive or root) | Returns `[]` — `ValueError` caught | R11 |
| T2.25 | Path has fewer than 3 parts | Returns `[]` | R11 |
| T2.26 | Context part is not in `["personal","professional","public"]` | Returns `[]` | R11 |
| T2.27 | Second path part is not `projects` | Returns `[]` | R11 |
| T2.28 | Derived project directory does not exist on disk | Returns `[]` | R11 |

### `strip_ide_selection(message)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T2.44 | Message contains one `<ide_selection>` block with a project path | Block stripped; rest of message preserved | |
| T2.45 | Message contains no `<ide_selection>` block | Message returned unchanged | |
| T2.46 | Message contains multiple `<ide_selection>` blocks | All blocks stripped; other content preserved | |

### `find_projects_in_message(cwd, message)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T2.29 | Message contains project name in hyphen form (`my-project`) | Project included in results | |
| T2.30 | Message contains project name in space form (`my project`) | Project included in results | |
| T2.31 | Message contains substring of a project name (not exact) | Project included — substring match is intentional behaviour | |
| T2.32 | No projects directory exists for a context | That context skipped, no crash | R11 |
| T2.33 | Message mentions no project names | Returns `[]` | R11 |

### `inject-context-claude.py` / `inject-context-memory.py` — `main()`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T2.34 | Project name in message, `CLAUDE.md` exists | Output includes label + content, exits 0 | |
| T2.35 | Project name in message, `_memory.md` exists | Output includes label + content, exits 0 | |
| T2.36 | Multiple projects matched | All injected, separated by `---` | |
| T2.37 | IDE fallback triggers (no message match, IDE file in project dir) | Project loaded via IDE path | |
| T2.38 | Project matched but `CLAUDE.md` / `_memory.md` missing | No output for that project, no crash | R11 |
| T2.39 | IDE fallback attempted but IDE file not in a project dir | No output, exits 0 | R11 |
| T2.40 | Both message and IDE match same project | Project appears only once (IDE fallback only runs when message lookup returns empty) | |
| T2.41 | Second turn (assistant entry in transcript) | Exits 0, no output | |
| T2.42 | Explicit project in message + `<ide_selection>` block containing a different project's path | Only explicit project injected; IDE selection project not loaded | |
| T2.43 | `<ide_selection>` block with project path, no explicit project name, no "opened file" annotation | No output — IDE selection alone does not trigger injection | |

---

## T3 — `test_save_conversation.py`

### `format_user_text(text)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T3.1 | Plain text with no special tags | Returned unchanged (stripped) | R10 |
| T3.2 | Text with `<system-reminder>...</system-reminder>` | Tag and content removed | R10 |
| T3.3 | Text with `<ide_opened_file>` annotation | Replaced with `` > `Opened in IDE` path `` | R10 |
| T3.4 | Text with `<ide_selection>` annotation | Replaced with `` > `Selected in IDE` lines N-M in path `` | R10 |
| T3.5 | Multiple `<system-reminder>` blocks in one message | All removed | R10 |
| T3.6 | `<ide_opened_file>` and `<system-reminder>` in same message | Both handled independently | R10 |
| T3.7 | Empty string input | Returns empty string | R11 |
| T3.8 | Text where tag spans multiple lines | Multiline match handled correctly (`(?s)` flag) | R10 |

### `extract_events_from_transcript(msg_order, msg_data)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T3.9 | 🧠 marker in assistant text segment | `"memory"` in events | R10 |
| T3.10 | 👤 marker in assistant text segment | `"profile"` in events | R10 |
| T3.11 | 🗂️ marker in assistant text segment | `"distill"` in events | R10 |
| T3.12 | ✅ marker in assistant text segment | `"task"` in events | R10 |
| T3.13 | 🔁 processed marker in assistant text | `"memory"` in processed | R10 |
| T3.14 | 🪪 processed marker | `"profile"` in processed | R10 |
| T3.15 | 📦 processed marker | `"distill"` in processed | R10 |
| T3.16 | 📋 processed marker | `"task"` in processed | R10 |
| T3.17 | Same event marker appears in two different assistant messages | Event type appears only once in list | R10 |
| T3.18 | Event marker appears in a user turn (not assistant) | Not captured | R10 |
| T3.19 | Only emoji present without full marker text (e.g. just `🧠`) | Not matched — full marker string required | R10 |
| T3.20 | No markers anywhere in transcript | Returns `([], [])` | R11 |

### `extract_projects_from_transcript(msg_order, msg_data)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T3.21 | First user message contains `project: my-project` | `"my-project"` in results | R10 |
| T3.22 | Tool call path contains `personal/projects/my-project/file.md` | `"my-project"` in results | R10 |
| T3.23 | Same project appears from both sources | Appears only once (deduped) | R10 |
| T3.24 | `project:` line appears in second user message (not first) | Not captured | R10 |
| T3.25 | No `project:` line and no tool paths | Returns `[]` | R11 |
| T3.26 | Tool call path is in `areas/` not `projects/` | Not matched | R10 |

### `clean_project_name(p)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T3.27 | Plain name `"my-project"` | Returned unchanged | R10 |
| T3.28 | Wikilink format `"[[my-project]]"` | Returns `"my-project"` | R10 |
| T3.29 | Name with surrounding whitespace | Stripped | R11 |
| T3.30 | Name wrapped in quotes `'"my-project"'` | Quotes stripped | R11 |

### `main()`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T3.31 | Valid transcript with ai-title | File written with correct frontmatter (title, session, projects, events) | R10 |
| T3.32 | Existing file for same session ID found | Date field preserved, old file deleted if renamed | R10 |
| T3.33 | stdin is empty | Exits 0, no file written | R11 |
| T3.34 | stdin is invalid JSON | Exits 0, no file written | R11 |
| T3.35 | `transcript_path` key missing | Exits 0, no file written | R11 |
| T3.36 | Transcript file does not exist | Exits 0, no file written | R11 |
| T3.37 | Transcript has no `ai-title` entry | Exits 0, no file written | R11 |
| T3.38 | `_conversations/` directory does not exist in `cwd` | Exits 0, no file written — prevents writing to wrong repo root | R11 |
| T3.39 | Transcript has messages but zero text segments | Frontmatter written, body effectively empty — no crash | R11 |

---

## T4 — `test_generate_pending_events.py`

### `parse_frontmatter(path)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T4.1 | File has valid frontmatter with `events` and `processed` | Both lists parsed correctly | R10 |
| T4.2 | File has frontmatter with only `events` | `processed` defaults to `[]` | R10 |
| T4.3 | File has UTF-8 BOM at start | Parsed correctly (`utf-8-sig` encoding) | R7 |
| T4.4 | File has no frontmatter (no opening `---`) | Returns `{events:[], processed:[]}` | R11 |
| T4.5 | File has opening `---` but no closing `---` | Reads until EOF without crash | R11 |
| T4.6 | `events` value is malformed JSON (e.g. `events: [memory`) | `events` stays `[]` — decode error swallowed | R11 |
| T4.7 | `processed` value is malformed JSON | `processed` stays `[]` | R11 |
| T4.8 | Frontmatter has neither `events` nor `processed` keys | Both default to `[]` | R11 |

### `main()`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T4.9 | Conversation has `events: ["memory"]`, no processed | Flagged — pending: memory | R10 |
| T4.10 | Conversation has `events: ["memory"]`, `processed: ["memory"]` | Not flagged | R10 |
| T4.11 | Conversation has `events: ["memory","distill"]`, `processed: ["memory"]` | Flagged — pending: distill only | R10 |
| T4.12 | Conversation has no events | Not flagged | R10 |
| T4.13 | Multiple pending conversations | Output sorted newest first by date | R7 |
| T4.14 | File with stem shorter than 10 chars (e.g. `notes.md`) | Skipped — not treated as conversation | R7 |
| T4.15 | `_conversations/` directory is empty | Output file written with "No pending events" message, no crash | R11 |
| T4.16 | `index.md` present in conversations directory | Excluded from scan | R7 |
| T4.17 | `pending-events.md` itself is in `_conversations/` | Does not self-reference — excluded by filename check | R7 |

---

## T5 — `test_generate_dashboard.py`

### `collect_resources(para_dir)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T5.1 | Normal `.md` file in resources root | Included as `[[stem]]` wikilink | R7 |
| T5.2 | Subdirectory with `index.md` | Included as `[[dir/index\|dir]]` wikilink | R7 |
| T5.3 | Subdirectory without `index.md`, contains `.md` files | Individual file wikilinks included | R7 |
| T5.4 | `tags/` subdirectory present | Skipped entirely — not included in results | R7 |
| T5.5 | `tags/` subdirectory contains `.md` files | Those files also excluded (directory skipped before iterating) | R7 |
| T5.6 | `index.md` at the resource root level | Excluded — not treated as a resource entry | R7 |
| T5.7 | File with non-`.md` extension in resources | Excluded | R7 |

### `parse_quick_status(memory_path)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T5.8 | `_memory.md` has `## Quick status` with `status:` and `next:` items | Both extracted correctly | R7 |
| T5.9 | `status:` line has trailing whitespace | Stripped | R7 |
| T5.10 | `_memory.md` does not exist | Returns `(None, [])` — no crash | R11 |
| T5.11 | `_memory.md` exists but has no `## Quick status` section | Returns `(None, [])` | R11 |
| T5.12 | `## Quick status` section has no `status:` line | Returns `(None, [])` for status, next items still parsed | R7 |
| T5.13 | Section ends at next `##` heading | Parsing stops at heading boundary correctly | R7 |

### `parse_frontmatter_tags(file_path)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T5.14 | File has `tags: [foo, bar]` | Returns `["foo", "bar"]` | R7 |
| T5.15 | Tags have `#` prefix (`tags: [#foo]`) | Returns `["foo"]` — prefix stripped | R7 |
| T5.16 | File has `tags: []` | Returns `[]` | R11 |
| T5.17 | File has no `tags` key | Returns `[]` | R11 |
| T5.18 | Tags are quoted strings (`tags: ["foo", "bar"]`) | Quotes stripped, returns `["foo", "bar"]` | R7 |

### `generate_tag_pages()` (via `main()`)

| # | Scenario | Expected | Req |
|---|---|---|---|
| T5.19 | Resources with tags exist | Each tag page has correct frontmatter (`context`, `para`, `tags`, `created`) and back link | R7 |
| T5.20 | Tag page already exists from previous run | `created` date preserved — rerun does not overwrite it | R7 |
| T5.21 | No tagged resources exist | `tags/` directory written but empty, no crash | R11 |

### Smoke test

| # | Scenario | Expected | Req |
|---|---|---|---|
| T5.22 | Run `generate-dashboard.py` against real vault | Exits 0, `dashboard.md` written | R7, R11 |

---

## T6 — `test_rag_embed.py`

### `make_point_id(file_path, heading, idx)`

| # | Scenario | Expected |
|---|---|---|
| T6.22 | Same inputs called twice | Identical output — deterministic |
| T6.23 | Different file paths, same heading and idx | Different IDs |
| T6.24 | Same file and heading, different idx | Different IDs |
| T6.25 | Any valid inputs | Output matches UUID format `8-4-4-4-12` lowercase hex |

### `should_skip(rel)`

| # | Scenario | Expected |
|---|---|---|
| T6.26 | Path has a part in SKIP_DIRS (e.g. `_conversations/note.md`) | Returns `True` |
| T6.27 | Filename is `index.md` (any location) | Returns `True` |
| T6.28 | Filename is `dashboard.md` | Returns `True` — generated file excluded from index |
| T6.29 | Valid content path (`personal/areas/health/note.md`) | Returns `False` |

### `split_sections(body)`

| # | Scenario | Expected |
|---|---|---|
| T6.13 | Body with two `##` headings | Returns preamble + two section tuples |
| T6.14 | Body with no headings | Returns `[("__preamble__", body)]` |
| T6.15 | Body starts immediately with a `##` heading | No preamble entry |
| T6.16 | Body has only a `#` (h1) heading | Not matched — treated as preamble |
| T6.17 | Body has a `###` heading | Matched — pattern covers h2 and h3 |

### `chunk_section(heading, body)`

| # | Scenario | Expected |
|---|---|---|
| T6.18 | Body fits within MAX_CHARS (1200) | Single chunk, idx 0 |
| T6.19 | Body exceeds MAX_CHARS | Multiple chunks; each advances MAX_CHARS − OVERLAP_CHARS (1000) |
| T6.20 | Heading is `__preamble__` | No `## ` prefix in chunk text |
| T6.21 | Normal heading | Chunk text prefixed with `## {heading}\n\n` |

### `main()` — graceful degradation

`ensure_collection` and `ollama_embed` are mocked; file I/O uses a `TemporaryDirectory` vault for T6.33–T6.34. `_embed.__file__` is temporarily redirected so `root = Path(__file__).parent.parent` resolves to the temp vault.

| # | Scenario | Expected | Req |
|---|---|---|---|
| T6.30 | `OLLAMA_HOST` empty | Prints "not configured", returns; `ensure_collection` never called | R12 |
| T6.31 | `QDRANT_HOST` empty | Prints "not configured", returns; `ensure_collection` never called | R12 |
| T6.32 | `ensure_collection` raises `RuntimeError` (Qdrant down) | Prints error to stderr, exits 1 | R12 |
| T6.33 | All `ollama_embed` calls raise `URLError` (Ollama down, Qdrant up) | `embed_failures > 0`, `total_chunks == 0` → exits 1 | R12 |
| T6.34 | First embed succeeds, second raises `URLError` | `total_chunks > 0` → exits 0; warning printed per failed chunk | R12 |

---

## T7 — `test_rag_search.py`

### `main()` — graceful degradation

`ollama_embed` and `qdrant_search` are mocked; env vars controlled via `patch.dict`. All paths return cleanly (exit 0) — callers (`/search`, `/maintain` option 5) receive a readable message rather than a traceback.

| # | Scenario | Expected | Req |
|---|---|---|---|
| T7.1 | `OLLAMA_HOST` empty | Prints "not configured", returns; `ollama_embed` never called | R12 |
| T7.2 | `QDRANT_HOST` empty | Prints "not configured", returns; `ollama_embed` never called | R12 |
| T7.3 | `ollama_embed` raises `URLError` | Prints "Ollama unreachable: ...", returns cleanly | R12 |
| T7.4 | `qdrant_search` raises `URLError` | Prints "Qdrant unreachable: ...", returns cleanly | R12 |
| T7.5 | Both services up (mocked) | Results printed to stdout; file path appears in output | R12 |

---

## T8 — `test_inject_context_rag.py`

`ollama_embed` and `qdrant_search` are mocked; env vars controlled via `patch.dict`; a `TemporaryDirectory` provides `cwd` with stub vault files.

### `extract_h1(path)`

| # | Scenario | Expected | Req |
|---|---|---|---|
| T8.1 | File has H1 after YAML frontmatter | Returns heading text — frontmatter state machine skips the block correctly | R11 |
| T8.2 | H1 line appears inside the frontmatter block | Not returned — `in_frontmatter` flag suppresses it; stem returned instead | R11 |
| T8.3 | File has no H1 within first 30 lines | Returns `path.stem` — early-exit guard triggers | R11 |
| T8.4 | File does not exist or has encoding error | Returns `path.stem` — `OSError`/`UnicodeDecodeError` caught silently | R11 |

### `main()` — graceful degradation

| # | Scenario | Expected | Req |
|---|---|---|---|
| T8.5 | `OLLAMA_HOST` not set | Exits 0, no output; `ollama_embed` never called | R12 |
| T8.6 | `QDRANT_HOST` not set | Exits 0, no output; `ollama_embed` never called | R12 |
| T8.7 | `prompt` field is empty or whitespace | Exits 0, no output | R12 |
| T8.8 | `ollama_embed` or `qdrant_search` raises `URLError` | Exits 0, no output | R12 |

### `main()` — filtering and deduplication

| # | Scenario | Expected | Req |
|---|---|---|---|
| T8.9 | Qdrant returns empty result list | Exits 0, no output — `seen` stays empty, no crash | R11 |
| T8.10 | All results below `SCORE_THRESHOLD` (0.55) | Exits 0, no output | R11 |
| T8.11 | Same `file_path` in two hits with scores 0.60 then 0.65 | Entry updated to 0.65 — `score > seen[fp]` branch exercised; highest score kept | R11 |
| T8.12 | Four distinct files above threshold | Only top 3 in output, ordered by score descending — `MAX_FILES` limit enforced | R11 |

### `main()` — output format

| # | Scenario | Expected | Req |
|---|---|---|---|
| T8.13 | Two results above threshold with known files | Output is exactly `## Relevant vault notes\n- {path} — {title}` per result; em dash and spacing correct; highest-score file first | R11 |

---

## Smoke tests (all scripts)

| Script | Smoke assertion | Req |
|---|---|---|
| `inject-profile.py` | Exits 0; output contains `_self/about.md` content | R6, R11 |
| `inject-corrections.py` | Exits 0; output contains `_self/corrections.md` content | R6, R11 |
| `inject-context-claude.py` | Exits 0 with a known project name in prompt | R11 |
| `inject-context-memory.py` | Exits 0 with a known project name in prompt | R11 |
| `save-conversation.py` | Exits 0 when given a valid transcript path | R10, R11 |
| `generate-pending-events.py` | Exits 0; `_conversations/pending-events.md` written | R7, R10, R11 |
| `generate-dashboard.py` | Exits 0; `dashboard.md` written | R7, R11 |
| `rag-embed.py` (no args) | Exits 0; Qdrant `second_brain` collection exists, chunk count > 0 — requires live Qdrant + Ollama (configure via `.env`) | R5 |
| `rag-embed.py` (no `.env`, no env vars) | Exits 0; prints "RAG not configured" — no network calls | R5 |
| `rag-search.py` | Exits 0 with a known query; at least one result printed — requires live Qdrant + Ollama (configure via `.env`) | R5 |
| `rag-search.py` (no `.env`, no env vars) | Exits 0; prints "RAG not configured" — no network calls | R5 |
| `inject-context-rag.py` (live services, `.env` configured) | Exits 0 with a real prompt; if results exist, output starts with `## Relevant vault notes` | R12 |
| `inject-context-rag.py` (no `.env`, no env vars) | Exits 0; no output — not configured path | R12 |
