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

4. **Update `## Quick status` in-place** — if the project's status or next actions have materially changed this session, update the `status:` line and `next:` list directly using Edit. This section is always current-state, never appended to.

5. **Consolidate new content into each target file** — using Edit, absorb new facts directly into the appropriate existing sections. Merge with existing bullets where there is overlap; update in-place where a fact supersedes an existing one; only add new content that has no existing home. If nothing new is worth persisting beyond what's already in a file, skip that file.

6. **Emit processed markers** — output on separate lines, only for what was actually written:
   - `🔁 [remember processed]` only if `_memory.md` was written
   - `🪪 [profile processed]` only if a `_self/` file was written
   - `📋 [task processed]` only if task-relevant content was captured

7. Briefly confirm what was written and what was skipped (one line per file).
