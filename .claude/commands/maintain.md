Vault health audit.

Ask the user which operation:

**(1) Generate artifacts** — run scripts locally, same as CI
**(2) Inbox processing** — route inbox items to the right PARA location
**(3) Event processing** — surface and process missed events from past conversations
**(4) Memory maintenance** — consolidate and budget AI-maintained files
**(5) Resource note maintenance** — deduplicate and cross-link resource notes
**(6) Reports** — automated scans, findings only, no edits

---

## Option 1 — Generate artifacts

Run all scripts in order:
- `python _scripts/generate-conversation-index.py`
- `python _scripts/generate-project-indices.py`
- `python _scripts/generate-dashboard.py`
- `python _scripts/generate-pending-events.py`
- `python _tests/test_hook_budget.py`

Report: what was regenerated and budget output summary.

---

## Option 2 — Inbox processing

Route items out of `_inbox/`. One file at a time — wait for confirmation before moving to the next.

1. List all files in `_inbox/`. If empty, report and stop.

2. For each file:
   a. Read the content.
   b. Infer context (`personal/`, `professional/`, `public/`), PARA category, and propose a destination path and slug.
   c. If the content looks like stable reference material, flag as a `/distill` candidate instead of proposing a direct path — do not route it yourself.
   d. Show the proposed destination (or distill flag) and wait for user confirmation.
   e. On confirm: move the file using Bash (`mv` or `Move-Item`), update frontmatter fields (`context`, `para`, `created`) as needed using Edit.
   f. On skip: leave the file in `_inbox/` and move to the next.

3. Report: how many items routed, how many flagged for `/distill`, how many skipped.

---

## Option 3 — Event processing

1. Read `_conversations/pending-events.md`. If empty or missing, report no pending events and stop.

2. For each pending conversation, one at a time:
   a. Read the conversation file.
   b. Find all 🧠, 👤, 🗂️, and ✅ marker lines and their descriptions.
   c. For 🧠 and ✅ markers: process as `/remember` would — append a `<!-- remembered: YYYY-MM-DD -->` block to the project `_memory.md` using Edit.
   d. For 👤 markers: route to `_self/` — behavioral observations and feedback corrections → `_self/rules.md`; profile facts → `_self/about.md`. Append a `<!-- remembered: YYYY-MM-DD -->` block using Edit.
   e. For 🗂️ markers: process as `/distill` would — draft note, show proposed path and content, wait for user confirmation before writing.
   f. On completion: update the conversation file's `processed` frontmatter field using Edit to reflect what was actioned. Token names: `memory` (🧠), `profile` (👤), `distill` (🗂️), `task` (✅) — all match their event type exactly.

3. Run `python _scripts/generate-pending-events.py` to refresh `_conversations/pending-events.md`.

4. Report: what was written, what was skipped, and how many conversations remain pending.

---

## Option 4 — Memory maintenance

Consolidate and budget AI-maintained files. Propose changes — apply only with user confirmation. Always use Edit, never Write.

1. **`_self/` consolidation** — check `_self/about.md` and `_self/rules.md` for:
   - Appended `<!-- remembered: YYYY-MM-DD -->` blocks — absorb into the appropriate sections, then remove the raw blocks
   - Duplicate bullets expressing the same trait from different angles — propose merging
   - `## Reflection` exceeding 20 bullets — propose grouping into labeled sub-clusters
   - Files over 80% of budget (8,000 chars) — identify candidates for condensing; flag as urgent if over 10,000 chars

2. **Project memory consolidation** — for each active project, if `_memory.md` exceeds 8,000 chars:
   - Read the full file — distinguish structured sections from raw appended blocks (`<!-- remembered: ... -->`)
   - Consolidate appended blocks into the appropriate sections
   - Route aging content: key decisions → create `decisions/D{n}-{slug}.md` and add a row to `decisions/index.md` (newest first); stable reference → skip or note for `/distill`; superseded items → delete
   - Target file size after consolidation: ≤ 5,000 chars
   - Propose the consolidated version for user confirmation before writing

---

## Option 5 — Resource note maintenance

Read and reason about resource notes. Propose changes — apply only with user confirmation. Always use Edit, never Write.

Read all notes in `resources/` across `personal/`, `professional/`, and `public/`. For each pair or group with overlapping titles, tags, or content:
- Summarize what each note covers
- Propose one of: merge into one note, extract a shared concept into a new note, or keep separate with a cross-link (`*→ See also: [[...]]*`)
- Show the proposed change (new or merged content) for user confirmation before writing
- On confirm: write using Edit (existing note) or Write (new note); add cross-links where relevant

> **Note:** This step reads all resource notes — token cost scales with vault size. Without RAG (Phase 1), this is the only cross-note similarity mechanism available. Once RAG Phase 1 is complete, replace the full read with a Qdrant similarity query.

---

## Option 6 — Reports

Run all checks and report findings. No edits.

1. **Structural audit** — for each active project under `personal/projects/`, `professional/projects/`, `public/projects/`, check:
   - Has all required files: `index.md`, `CLAUDE.md`, `_memory.md`?
   - Has significant design history → has `decisions/` folder with `index.md`?
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
