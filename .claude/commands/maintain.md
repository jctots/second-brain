Vault health audit. Execute in order:

## Step 1 — Run scripts and collect budget data

Run all scripts:
- `python _scripts/index-conversations.py`
- `python _scripts/update-project-indexes.py`
- `python _tests/test_r6_hook_budget.py`

Collect budget output for use in steps 4 and 5.

---

## Step 2 — Review AI-maintained memory files

Find all AI-maintained vault memory files:
- `_self/about.md`, `_self/rules.md`
- For each active project (any folder under `personal/projects/`, `professional/projects/`, `public/projects/` containing a `_memory.md`): that project's `_memory.md`

For each file:
- Read the summary section (content above `<!-- extended -->`, or full file if no marker)
- Note the last-modified date
- Flag with ⚠️ if last modified more than 30 days ago

Print each file's summary section in full, grouped by file, with path and last-modified date as header. Do not summarize — show raw content.

After all files are shown, list flagged files and invite the user to identify what needs updating. Do not make edits — report only.

---

## Step 3 — Workspace memory violation check

Locate the Claude workspace memory directory for this repo: `~/.claude/projects/{encoded-repo-path}/memory/`. Read `MEMORY.md`. If any files other than `MEMORY.md` exist in that directory, flag them with 🚨 — workspace memory is retired. List filenames and content so the user can decide to migrate or delete.

---

## Step 4 — Consolidate `_self/` files

Using the budget output from step 1:
- **Deduplication**: check for bullets in `_self/about.md` and `_self/rules.md` that express the same trait from different angles — merge in-place.
- **Consolidation**: if `## Reflection` in `about.md` exceeds 20 bullets, group related bullets into labeled sub-clusters.
- If either file is over 80%, identify candidates for condensing and offer to apply. Flag as urgent if over 9,500 chars.
- Apply all changes only with confirmation. Always use Edit — never Write.

---

## Step 5 — Project file budget management

For each active project, using the budget output from step 1: if `CLAUDE.md` or `_memory.md` exceeds 80% (7,600 chars), identify candidates for demotion and offer to apply. Demotion options: move to extended section or delete if clearly stale. Always use Edit — never Write.

---

## Step 6 — Project structural audit

For each active project found in step 2, check:
- Has all required files: `index.md`, `CLAUDE.md`, `_memory.md`?
- `CLAUDE.md` contains an "On sync memory" section?
- `_memory.md` uses fixed-sections-in-place pattern (Current status, Key decisions, Open questions)?
- Has significant design history → has `decisions.md`?
- Has stable operational reference → has `reference.md`?

Scan for cross-pollination: note any pattern, convention, or file in one project absent in another where it would be useful.

Report as a table:

| Project | Missing files | CLAUDE.md gaps | _memory.md pattern | Cross-pollination candidates |
|---|---|---|---|---|

---

## Step 7 — PARA lifecycle check

For each active project found in step 2, apply the lifecycle test from root `CLAUDE.md`:
- Ask: *"Is there a defining goal still being worked toward?"*
- If no defining goal and no open questions → flag as area candidate
- If `_memory.md` has no open questions and no recent state changes → flag for review

Flag mismatches as: _"[project] may fit `areas/` better — no active goal found."_ Do not move anything — report only.

---

## Step 8 — Inbox aging

Scan `_inbox/` for files older than 14 days (compare `created` frontmatter or filename date against today). List them with age — do not move or delete, just surface for review.

---

## Step 9 — Conversation frontmatter

Scan `_conversations/` for files with an empty or missing `projects` frontmatter field. List them — do not infer or modify. Candidates for manual tagging.

---

## Step 10 — Queue retrospective

Identify conversations in `_conversations/` not referenced in either `_inbox/distill-queue.md` or `_inbox/memory-queue.md` (truly unprocessed — no `/remember` was run). Limit to the 10 most recent by filename date.

For each unprocessed conversation found, scan for missed distill and memory queue candidates — apply the same criteria as the during-conversation checks in root `CLAUDE.md`. Append any candidates found to the appropriate queue file using Edit.

---

## Step 11 — Report

Summarise: index regeneration status, budget status of all files (flag any over 80% or over limit), memory files reviewed and flagged, structural audit table, PARA lifecycle flags, inbox items needing attention, conversation files missing frontmatter, and what was added to the queues in step 10.
