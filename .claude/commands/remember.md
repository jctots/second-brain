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

6. **Review `## Next Actions` items** — if the list has items, first close any that were clearly completed this session (no prompt needed). Then display all remaining items numbered, and ask the user using AskUserQuestion with two options (use Other for selective actions: `close 1, 3` to remove specific items, or `handle 1, 3` to address specific items in conversation now):
   - "All still open — keep all"
   - "All done — close all"

   Interpret Other input: `close N[, N...]` → remove those items; `handle N[, N...]` → address each in conversation then remove them. Skip this step entirely if `## Next Actions` is empty after auto-closing completed items.

7. **Emit processed markers** — output on separate lines, only for what was actually written:
   - `🔁 [remember processed]` only if `_memory.md` was written
   - `🪪 [profile processed]` only if a `_self/` file was written
   - `📋 [task processed]` only if task-relevant content was captured

8. **Budget check** — run `wc -m {files-written}` to get character counts for every file written this session. If any file exceeds 8,000 chars, emit one line per offending file:
   `⚠️ {relative-path} is {N} chars — over 8,000 warn threshold; run /maintain option 4`

9. Briefly confirm what was written and what was skipped (one line per file).
