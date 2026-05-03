Process the distill queue into durable vault notes. Execute these steps in order:

1. Read `_inbox/distill-queue.md`. If the file is missing or empty, tell the user and stop.

2. For each pending entry, one at a time:
   a. Read the source conversation file referenced in the entry.
   b. Draft the note content — structured, concise, suitable for `areas/` or `resources/`.
   c. Show: proposed path, draft content, and a one-line reason for placing it there.
   d. Engage interactively — the user may add context, redirect scope, change the path, or ask for revisions. Iterate until the user explicitly confirms or skips the item.
   e. On confirm: write the note (Edit if the file exists, Write if new). If a new file is created, add it to `dashboard.md`.
   f. On skip: leave the entry in the queue unchanged.

3. After all entries are processed, remove only the confirmed entries from `_inbox/distill-queue.md` using Edit. Skipped entries remain.

4. Briefly list what was written and what remains in the queue.
