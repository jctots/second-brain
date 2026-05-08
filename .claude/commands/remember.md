Save context from the current conversation to persistent storage. Execute in order:

1. **Scan the conversation for 👤 profile content** — quickly check whether this conversation contains profile facts or behavioral observations worth persisting to `_self/`. This determines which files to read upfront.

2. **Read target files upfront** — always read the active project's `_memory.md`. If profile content is likely, also read `_self/about.md` and `_self/rules.md`.

3. **Make a judgment pass over this conversation** — review the full conversation and identify what is worth persisting. Look for:
   - Project state changes (decisions made, milestones reached, blockers hit)
   - Open questions that remain unresolved
   - Key decisions with rationale
   - Completed tasks or next actions the user should track
   - 👤 profile facts → `_self/about.md`; behavioral corrections or feedback rules → `_self/rules.md`

   Do not limit to 🧠 or 👤 markers — use your judgment. Markers are visual signals, not the authoritative source.

4. **Append a `<!-- remembered: YYYY-MM-DD -->` block to each target file** — using Edit (never Write), one edit per file:

   ```
   <!-- remembered: YYYY-MM-DD -->
   - [fact or decision worth keeping]
   - [fact or decision worth keeping]
   ```

   If nothing new is worth persisting beyond what's already in a file, skip that file.

5. **Emit processed markers** — output on separate lines, only for what was actually written:
   - `🔁 [remember processed]` only if `_memory.md` was written
   - `🪪 [profile processed]` only if a `_self/` file was written
   - `📋 [task processed]` only if task-relevant content was captured

6. Briefly confirm what was written and what was skipped (one line per file).
