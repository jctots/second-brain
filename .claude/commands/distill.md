Process distill events from the current conversation into durable vault notes. Execute in order:

1. **Scan for distill events** — look back through this conversation for 🗂️ `[distill event]` markers. If none found, tell the user and stop.

2. **Process each event, one at a time:**
   a. Draft the note content — structured, concise, suitable for `resources/`.
   b. Show: proposed path, draft content, and a one-line reason for placing it there.
   c. Engage interactively — the user may add context, redirect scope, change the path, or ask for revisions. Iterate until the user explicitly confirms or skips the item.
   d. On confirm: write the note (Edit if the file exists, Write if new). If a new file is created, add it to `dashboard.md`.
   e. On skip: move to the next item.

3. **Emit processed marker** — output `📦 [distill processed]` on its own line.

4. Briefly confirm what was written and what was skipped.
