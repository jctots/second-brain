Vault health audit.

Ask the user which operation:

**(1) Generate artifacts** — run scripts locally, same as CI
**(2) Pending events** — surface and process missed events from past conversations
**(3) Reports** — automated scans, findings only, no edits
**(4) Reviews** — read and reason about content, propose changes for user confirmation

---

## Option 1 — Generate artifacts

Run all scripts in order:
- `python _scripts/index-conversations.py`
- `python _scripts/update-project-indexes.py`
- `python _scripts/generate-pending-events.py`
- `python _tests/test_r6_hook_budget.py`

Report: what was regenerated and budget output summary.

---

## Option 2 — Pending events

1. Read `_conversations/pending-events.md`. If empty or missing, report no pending events and stop.

2. For each pending conversation, one at a time:
   a. Read the conversation file.
   b. Find all 🧠, 🗂️, and ✅ marker lines and their descriptions.
   c. For 🧠 and ✅ markers: process as `/remember` would — route to the correct target file and write using Edit.
   d. For 🗂️ markers: process as `/distill` would — draft note, show proposed path and content, wait for user confirmation before writing.
   e. On completion: update the conversation file's `processed` frontmatter field using Edit to reflect what was actioned.

3. Run `python _scripts/generate-pending-events.py` to refresh `_conversations/pending-events.md`.

4. Report: what was written, what was skipped, and how many conversations remain pending.

---

## Option 3 — Reports

Run all checks and report findings. No edits.

1. **Structural audit** — for each active project under `personal/projects/`, `professional/projects/`, `public/projects/`, check:
   - Has all required files: `index.md`, `CLAUDE.md`, `_memory.md`?
   - Has significant design history → has `decisions.md`?
   - Has stable operational reference → has `reference.md`?
   - Scan for cross-pollination: note any pattern, convention, or file in one project absent in another where it would be useful.

   Report as a table:

   | Project | Missing files | Cross-pollination candidates |
   |---|---|---|

2. **PARA lifecycle** — scan all items across `projects/` and `areas/` in every context. Apply the full transition table:

   | Check | Flag |
   |---|---|
   | `projects/` with no defining goal and no open questions | → `areas/` candidate |
   | `projects/` with goal met and no ongoing responsibility | → `archive/` candidate |
   | `areas/` with an active bounded goal | → `projects/` candidate |
   | `areas/` with responsibility fully ended | → `archive/` candidate |
   | `projects/` or `areas/` that is pure stable reference | → extract to `resources/` via `/distill` |

   Do not move anything — report only.

3. **Inbox aging** — scan `_inbox/` for files older than 14 days (compare `created` frontmatter or filename date against today). List with age — do not move or delete.

4. **Conversation frontmatter** — scan `_conversations/` for files with an empty or missing `projects` field. List as candidates for manual tagging.

5. **Workspace memory violations** — locate `~/.claude/projects/{encoded-repo-path}/memory/`. Read `MEMORY.md`. If any files other than `MEMORY.md` exist, flag with 🚨 and list filenames and content so the user can decide to migrate or delete.

---

## Option 4 — Reviews

Read and reason about content. Propose changes — apply only with user confirmation. Always use Edit, never Write.

1. **Memory file review** — find all AI-maintained files: `_self/about.md`, `_self/rules.md`, and each active project's `_memory.md`. For each:
   - Read the summary section (above `<!-- extended -->`, or full file if no marker)
   - Note last-modified date — flag with ⚠️ if older than 30 days
   - Print content in full, grouped by file. Do not summarize — show raw content.
   - After all files shown, invite the user to identify what needs updating.

2. **`_self/` consolidation** — check `_self/about.md` and `_self/rules.md` for:
   - Duplicate bullets expressing the same trait from different angles — propose merging
   - `## Reflection` exceeding 20 bullets — propose grouping into labeled sub-clusters
   - Files over 80% of budget — identify candidates for condensing; flag as urgent if over 9,500 chars

3. **Project budget management** — for each active project, if `CLAUDE.md` or `_memory.md` exceeds 80% (7,600 chars), identify candidates for demotion. Options: move to extended section or delete if clearly stale.
