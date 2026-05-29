Save context from the current conversation to persistent storage. Execute in order:

1. **Scan the conversation for profile content** — quickly check whether this conversation contains profile facts or behavioral observations worth persisting to `_self/`. This determines which files to read upfront.

2. **Read target files upfront** — always read the active project's `_memory.md`. If profile content is likely, also read `_self/about.md`, `_self/corrections.md`, and `_self/reflection.md`.

3. **Make a judgment pass over this conversation** — review the full conversation and identify what is worth persisting. Look for:
   - Project state changes (decisions made, milestones reached, blockers hit)
   - Open questions that remain unresolved
   - Key decisions with rationale
   - Completed tasks or next actions the user should track
   - Profile facts → `_self/about.md`
   - Behavioral corrections, feedback rules, or recurring failures with a Claude-side prevention → `_self/corrections.md` (for failures, use the format: **What happened** / **Root cause** / **Prevention**)
   - User-side observations (failure or self-awareness, no Claude action) → `_self/reflection.md ## Behavioral patterns`

   Do not limit to 🧠 or 👤 markers — use your judgment. Markers are visual signals, not the authoritative source.

4. **Consolidate new content into each target file** — using Edit, absorb new facts directly into the appropriate existing sections of `_memory.md` (`## Current Status`, `## Key decisions`, `## Open questions`, and any project-specific sections) and `_self/` files. Merge with existing bullets where there is overlap; update in-place where a fact supersedes an existing one; only add new content that has no existing home. If nothing new is worth persisting beyond what's already in a file, skip that file.

5. **Update `## Snapshot` and `## Next Actions` in-place** — if the project's status or next actions have materially changed this session, update the `## Snapshot` text and `## Next Actions` list directly using Edit. Both sections are always current-state, never appended to. Write plain bullets in `## Next Actions` — no emoji prefix.

6. **Identify and close completed `## Next Actions` items** — identify any items that were clearly completed this session. Remove each from `_memory.md` (Edit, no prompt needed). Keep a list of the removed titles for step 8.

7. **Sync to Vikunja** — requires Vikunja MCP configured (`.mcp.json` at project root). Attempt the MCP call; if it fails (MCP unavailable, auth error, network), skip this step and note the failure. Otherwise:
   a. Determine the Vikunja project name from the vault project folder slug (e.g. `home-lab-infrastructure`).
   b. Check whether a Vikunja project with that name exists. If not, create it.
   c. Fetch all open tasks from that Vikunja project.
   d. For each item currently in `## Next Actions`: if no open Vikunja task with a matching title exists, create one.
   e. For each title removed in step 6: close the matching open Vikunja task.

8. **Emit processed markers** — output on separate lines, only for what was actually written:
   - `🔁 [remember processed]` only if `_memory.md` was written
   - `🪪 [profile processed]` only if a `_self/` file was written
   - `📋 [task processed]` only if task-relevant content was captured

9. **Budget check** — run `wc -m {files-written}` to get character counts for every file written this session. If any file exceeds 8,000 chars, emit one line per offending file:
    `⚠️ {relative-path} is {N} chars — over 8,000 warn threshold; run /maintain option 5`

10. Briefly confirm what was written and what was skipped (one line per file).

11. **Generate handover prompt** — if items remain in `## Next Actions` after step 6, generate a copy-pastable block the user can paste at the start of the next session. Include a one-liner summary of what was accomplished this session, then list the open items. Format as a fenced code block:

   ```
   project: <project-name>

   Last session: <one-line summary of what was done>.

   Continuing next actions:
   1. <item>
   2. <item>
   ...
   ```

   Display the handover prompt and stop — do not close or modify the remaining items. They will be handled in the session where the handover prompt is used. Skip step 7 entirely if `## Next Actions` is empty after step 6.

