Save context from the current conversation to persistent storage.

1. **Prepare** — Read the active project's `_memory.md` only if it was not already
   injected this session. `_self/about.md` and `_self/corrections.md` are injected on
   the first turn — do not re-read them; read `_self/reflection.md` only if this
   conversation contains user-side self-observations. Then make a judgment pass over
   the full conversation to identify what is worth persisting:
   - Project state changes, decisions with rationale, open questions, next actions
     → `_memory.md`
   - Profile facts → `_self/about.md`; behavioral corrections, feedback rules,
     failure patterns → `_self/corrections.md`; user-side self-awareness (no
     Claude action) → `_self/reflection.md`

   Markers (🧠, 👤) are signals, not the authoritative source — use judgment.

   Also scan for missed 🗂️ distill events: review the full conversation for generalizable insights not already marked — frameworks, principles, patterns, tool comparisons, mental models that apply beyond this project. Emit any missed `🗂️ [distill event]:` markers now before proceeding.

2. **Write** — Absorb new facts into each target file using Edit:
   - In `_memory.md`:
     - `## Snapshot`: overwrite with a single current-state line.
     - `## Next Actions`: update in-place. Remove items clearly completed this session — keep a list of removed titles for step 3.
     - `## Working Context`: **replace**, do not accumulate. Write one paragraph covering the current session. Prior-session detail lives in git history, not here.
     - `## Key decisions`: if a `decisions/` folder already exists for this project, add new decisions directly to `decisions/index.md` (D# row, newest-first, increment from current top row) — do not accumulate inline. Keep `## Key decisions` as a single pointer line only. If no `decisions/` folder exists yet and the section exceeds ~8 bullets, create the folder per CLAUDE.md and route the oldest stable ones there.
     - `## Open questions`: merge; remove resolved items.
   - In `_self/` files: merge with existing bullets; update in-place where a fact supersedes; only add content with no existing home.
   - Skip a file entirely if nothing new is worth persisting.

2.5. **Route on threshold** — `## Key decisions`, `## Next Actions`, and
   `## Open questions` only ever merge, so `_memory.md` grows monotonically unless
   something routes content out. Do that here, for the active project only, when it
   is actually needed:

   Run `python _tests/test_hook_budget.py {context}/projects/{project}`. Trigger if
   either the project's `_memory.md` is at WARN or FAIL, **or** `## Key decisions`
   exceeds ~8 bullets. Otherwise skip and say so in one line.

   When triggered, apply `/maintain` option 5.2 to this project only:
   - key decisions → `decisions/D{n}-{slug}.md` + a row in `decisions/index.md`
   - stable reference (config, URLs, inventories) → `reference.md` or the project
     equivalent (`architecture.md`, `requirements.md`)
   - cross-project generalizable insight → flag as a `/distill` candidate
   - superseded items → delete

   Propose the routing and wait for confirmation before writing. Vault-wide
   consolidation and `_self/` files stay with `/maintain` option 5 — this step never
   touches another project.

3. **Sync to Vikunja** — Requires Vikunja MCP (`.mcp.json`). Skip on any MCP
   failure; note the failure. Otherwise:
   a. Find or create the Vikunja project matching the vault folder slug (e.g.
      `home-lab-infrastructure`).
   b. Fetch open tasks via `list_tasks` (returns up to 50 tasks). Then call
      `get_task(N)` **only** for `[#N]` IDs in `## Next Actions` that `list_tasks`
      did not return — those are the ones past the 50-item page limit. Every other
      ID is already covered by the single `list_tasks` result; calling `get_task`
      for it is a redundant round-trip and is the main cost of this step. Usually
      this means zero `get_task` calls.
   c. **Vikunja → memory:** Vikunja is the source of truth for the task list.
      - For items with `[#N]`: if `get_task(N)` shows `done: true`, remove the
        item from `## Next Actions` and add its ID N to the removed list.
      - Add to `## Next Actions` any open task from `list_tasks` that has no
        matching entry there yet (copy title verbatim; append `[#N]`).
   d. **Memory → Vikunja (close):** For each ID N in the removed list, call
      `complete_task(N)` directly — no title matching needed.
   e. **Memory → Vikunja (create):** Call `batch_create_tasks` in one call for
      all `## Next Actions` items with no `[#N]` suffix. Append `[#N]` to each
      item in `_memory.md` using the IDs returned.

4. **Report** — Emit on separate lines, only for what was actually written:
   - `🔁 [remember processed]` if `_memory.md` was written
   - `🪪 [profile processed]` if any `_self/` file was written
   - `📋 [task processed]` if task content was captured

   Run `python _tests/test_hook_budget.py {context}/projects/{project}` — it applies
   the configured thresholds and counts the injector label, which a raw character
   count does not. Report any WARN or FAIL line, and if step 2.5 did not already
   route the content: `⚠️ {path} — run /maintain option 5`
   Confirm what was written and skipped (one line per file).

   No handover block. `inject-context-memory.py` loads `_memory.md`, including
   `## Next Actions`, on the next session's first turn.
