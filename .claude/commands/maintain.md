Vault health audit.

Ask the user which operation:

**(1) Generate artifacts** — run scripts locally, same as CI
**(2) Tasks sync** — pull task state from Vikunja and reconcile `## Next Actions` across all active projects
**(3) Inbox processing** — route inbox items to the right PARA location
**(4) Event processing** — surface and process missed events from past conversations
**(5) Memory maintenance** — condense AI-maintained files that have grown large
**(6) Resource note maintenance** — deduplicate and cross-link resource notes
**(7) Documentation maintenance** — consistency check across implementation, SE docs, and README
**(8) Roadmap maintenance** — research landscape, prune implemented items, update limitations-and-roadmap.md
**(9) Reports** — automated scans, findings only, no edits

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

## Option 2 — Service sync

Pull task state from Vikunja and reconcile `## Next Actions` across all active projects. Requires Vikunja MCP configured (`.mcp.json` at project root). Attempt the MCP call; if it fails, report and stop.

1. Read all active project paths from the `## Active Projects` context block. Extract the folder name (last path segment) for each — this is the Vikunja project name.

2. For each project: query Vikunja for all tasks in the project matching the folder name. Separate into open and closed. Always query fresh — do not reuse task results from an earlier `/remember` or `/maintain` run in the same session, as the user may have closed tasks in between.

3. For each project `_memory.md`:
   - Closed Vikunja tasks matching an entry in `## Next Actions` → remove directly.
   - Open Vikunja tasks not found in `## Next Actions` → add directly.

4. Write all changes and report: removed (completed on Vikunja), added (Vikunja-only), no-change.

---

## Option 3 — Inbox processing

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

## Option 4 — Event processing

1. Read `_conversations/pending-events.md`. If empty or missing, report no pending events and stop.

2. For each pending conversation, one at a time:
   a. Read the conversation file.
   b. Find all 🧠, 👤, 🗂️, and ✅ marker lines and their descriptions.
   c. For 🧠 and ✅ markers: process as `/remember` step 2 would — merge new facts into `_memory.md` in-place using Edit. No append blocks.
   d. For 👤 markers: route to `_self/` — behavioral corrections, feedback rules, or recurring failures with a Claude-side prevention → `_self/corrections.md`; profile facts → `_self/about.md`; user-side observations (failure or self-awareness, no Claude action) → `_self/reflection.md`. Merge in-place using Edit. No append blocks.
   e. For 🗂️ markers: process as `/distill` would — draft note, show proposed path and content, wait for user confirmation before writing.
   f. On completion: update the conversation file's `processed` frontmatter field using Edit to reflect what was actioned. Token names: `memory` (🧠), `profile` (👤), `distill` (🗂️), `task` (✅) — all match their event type exactly.

3. Run `python _scripts/generate-pending-events.py` to refresh `_conversations/pending-events.md`.

4. Report: what was written, what was skipped, and how many conversations remain pending.

---

## Option 5 — Memory maintenance

Exceptional maintenance for AI-maintained files that have grown large with genuine content. Propose changes — apply only with user confirmation. Target file size after consolidation: ≤ 5,000 chars.

0. **Size survey** — run `python _tests/test_hook_budget.py` to get current sizes and identify which files are over threshold before doing any work. Report the output; use it to prioritise what to consolidate.

1. **`_self/` consolidation** — for each large `_self/` file (`about.md`, `corrections.md`, `reflection.md`):
   - Duplicate or mergeable bullets expressing the same trait from different angles — propose merging
   - `## Behavioral patterns` in `reflection.md` exceeding 20 bullets — propose grouping into labeled sub-clusters

2. **Project memory consolidation** — for each active project with a large `_memory.md`:
   - Route aging content: key decisions → create `decisions/D{n}-{slug}.md` and add a row to `decisions/index.md` (newest first)
   - stable reference (config, deployment details, inventories, URLs) → move to `reference.md` or the project-equivalent stable doc (`architecture.md`, `requirements.md`, etc.)
   - cross-project generalizable insight → flag as a `/distill` candidate (creates a resource note; removes from `_memory.md`)
   - superseded items → delete

3. **Next Actions staleness audit** — surface implied next actions not yet captured in `## Next Actions`. For each active project:
   a. Read `_memory.md` — scan `## Working Context` and `## Open questions` for anything that implies a pending action not already listed in `## Next Actions`.
   b. Read `_conversations/pending-events.md` — find any unprocessed ✅ markers for this project that haven't been captured as Next Actions.
   c. Propose additions as plain bullets. Show proposed additions grouped by project and wait for user confirmation before writing to `_memory.md`.

---

## Option 6 — Resource note maintenance

Use Qdrant via `rag-search.py` to find overlapping notes without loading all resource content into context. Propose changes — apply only with user confirmation. Always use Edit, never Write.

1. List all notes under `resources/` across `personal/`, `professional/`, and `public/`.
2. For each note, run `python _scripts/rag-search.py "<note title and topic>" --top 5` and check whether any top results come from a *different* resource note.
3. Collect all flagged pairs (note A ↔ note B appearing in each other's top results).
4. For each flagged pair: read both notes, summarize what each covers, then propose one of:
   - Merge into one note
   - Extract a shared concept into a new resource note
   - Keep separate with a cross-link (`*→ See also: [[...]]*`)
5. Show the proposed change for user confirmation before writing.
   On confirm: use Edit for existing notes, Write for new notes.

**Score calibration note:** Similarity scores from Qdrant depend on the embedding model and content. Before treating any score as a threshold, run a few test queries on notes you know are similar and different, observe the score range, then use judgment. Do not apply a fixed cutoff without calibrating first.

---

## Option 7 — Documentation maintenance

Consistency check in three cascading layers. Each layer only runs if the previous layer produced changes.

**Pattern per layer:**
- Surface each inconsistency one at a time
- For each: ask the user whether the implementation or the documentation is correct, or whether it is a planned change not yet implemented
- Record the user's answer — do not apply any changes yet
- After all inconsistencies in the layer are resolved: show all proposed changes together and wait for confirmation before writing

---

### Layer 1 — Implementation vs. SE docs

Compare the actual implemented system against `requirements.md`, `architecture.md`, and `verification.md` (the SE document set for `second-brain-setup`).

**What to read:**
- `personal/projects/second-brain-setup/requirements.md`
- `personal/projects/second-brain-setup/architecture.md`
- `personal/projects/second-brain-setup/verification.md`
- All scripts in `_scripts/`
- All tests in `_tests/`
- Hooks configured in `.claude/settings.json` or `.claude/settings.local.json`
- Slash commands in `.claude/commands/`

**What to check:**
- Does each requirement (R#) have a corresponding implementation?
- Does each architecture component (A#) match what the scripts and hooks actually do?
- Does each test scenario (T#.#) match the current script behavior?
- Are there implemented behaviors with no corresponding requirement, architecture component, or test?

**Per inconsistency, ask:**
> "Inconsistency: [description]. Is the [implementation / documentation] correct, or is this a planned change not yet implemented?"

Wait for the user's answer before moving to the next inconsistency.

After all inconsistencies: present a consolidated list of proposed changes (implementation edits or doc edits) and wait for user confirmation before writing.

If no inconsistencies found, report and skip layers 2 and 3.

---

### Layer 2 — SE docs vs. docs/ and root .md files

Run only if layer 1 produced changes. Compare the agreed state from layer 1 against:
- All files in `docs/` (if the folder exists)
- All `.md` files in the repo root **except** `README.md` and `dashboard.md`

**What to check:**
- Do these files reference requirements, components, or behaviors that were updated in layer 1?
- Are there descriptions, diagrams, or references that now contradict the agreed state?

Same pattern: surface each inconsistency, ask implementation vs. documentation, record answer, propose all changes together after all inconsistencies are resolved.

If no inconsistencies found, report and skip layer 3.

---

### Layer 3 — Root README

Run only if layer 2 produced changes. Compare the agreed state from layers 1–2 against `README.md`.

**What to check:**
- Does `README.md` describe features, components, or behaviors that were updated in layers 1–2?
- Are there sections that now contradict the agreed state?

Same pattern: surface each inconsistency, ask implementation vs. documentation, record answer, propose all changes together after all inconsistencies are resolved.

---

## Option 8 — Roadmap maintenance

Research the PKM + AI landscape, prune implemented items, and update `docs/limitations-and-roadmap.md`. Propose all changes — apply only with user confirmation. Always use Edit, never Write (unless adding a net-new roadmap item that doesn't exist yet).

1. **Understand current state** — read `personal/projects/second-brain-setup/roadmap.md` and `personal/projects/second-brain-setup/architecture.md`. Build a list of all roadmap items and cross-check which are already reflected in the implemented components described in `architecture.md`.

2. **Research** — web-search for similar PKM + AI setups and tools in the current landscape. Focus on: what they offer that sbs doesn't, what sbs has that's unique, and gaps that appear across the field.

3. **Prune roadmap.md** — cross-check each item against the current implementation list from step 1:
   - Items fully implemented → propose removal or an "implemented" annotation
   - Competitive landscape section → propose updates based on research findings
   - New gaps from research worth tracking → propose as new items using the existing item structure (What / Why / Reuse candidate / Starter prompt)

   Show all proposed roadmap changes for user confirmation before writing.

4. **Update limitations-and-roadmap.md** — read `docs/limitations-and-roadmap.md` and compare against implemented state:
   - Near-term / medium-term items already shipped → check them off (`[x]`)
   - Items no longer relevant → propose removal
   - Research candidates that belong in the planned sections → propose additions under the appropriate horizon

   Show all proposed limitations-and-roadmap.md changes for user confirmation before writing.

---

## Option 9 — Reports

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
