Save context from the current conversation to persistent storage.

1. **Prepare** — Read the active project's `_memory.md`. If this conversation
   contains profile facts or behavioral observations, also read `_self/about.md`,
   `_self/corrections.md`, and `_self/reflection.md`. Then make a judgment pass
   over the full conversation to identify what is worth persisting:
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

3. **Sync to Vikunja** — Requires Vikunja MCP (`.mcp.json`). Skip on any MCP
   failure; note the failure. Otherwise:
   a. Find or create the Vikunja project matching the vault folder slug (e.g.
      `home-lab-infrastructure`).
   b. Fetch open tasks via `list_tasks` (returns up to 50 tasks). For any
      `## Next Actions` item that already has a `[#N]` suffix, also call
      `get_task(N)` directly — this covers tasks beyond the 50-item page limit.
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

   Run `wc -m` on each file written. Flag any over 8,000 chars:
   `⚠️ {path} is {N} chars — run /maintain option 5`
   Confirm what was written and skipped (one line per file).

5. **Handover** — If `## Next Actions` is non-empty after step 3, generate a
   copy-pastable block:

   ```
   project: <project-name>

   Last session: <one-line summary>.

   Continuing next actions:
   1. <item>
   ...
   ```
