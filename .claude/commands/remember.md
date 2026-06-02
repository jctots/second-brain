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

2. **Write** — Absorb new facts into each target file using Edit:
   - In `_memory.md`: merge into existing sections (`## Current Status`,
     `## Key decisions`, `## Open questions`); update `## Snapshot` to a
     single current-state line; update `## Next Actions` in-place (plain
     bullets, never appended to). Remove items clearly completed this session
     — keep a list of removed titles for step 3.
   - In `_self/` files: merge with existing bullets; update in-place where a
     fact supersedes; only add content with no existing home.
   - Skip a file entirely if nothing new is worth persisting.

3. **Sync to Vikunja** — Requires Vikunja MCP (`.mcp.json`). Skip on any MCP
   failure; note the failure. Otherwise:
   a. Find or create the Vikunja project matching the vault folder slug (e.g.
      `home-lab-infrastructure`).
   b. Fetch all tasks (open and done) from that project.
   c. **Vikunja → memory:** Remove from `## Next Actions` any item whose
      matching Vikunja task is marked done. Add those titles to the removed list.
   d. **Memory → Vikunja (close):** Close the matching Vikunja task for each
      title in the removed list.
   e. **Memory → Vikunja (create):** Call `batch_create_tasks` in one call for
      all `## Next Actions` items with no matching Vikunja task (open or done).

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
