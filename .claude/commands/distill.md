Process pending queues into durable vault notes. Execute in order:

## Step 0 — Process orphaned memory queue entries

Read `_inbox/memory-queue.md`. If it contains entries from conversations other than the current one (entries that `/remember` did not process), handle them now:

- Group by target file.
- For each target file: read the file, consolidate candidates using the context snippet. Do not reload source conversations unless the snippet is clearly insufficient.
- Apply the memory filter: `_memory.md` captures current state, open questions, and active constraints — not implementation documentation. Skip candidates that describe *how something works* rather than *what has changed or what is still open*.
- Write using Edit (never Write).
- Remove processed entries from `_inbox/memory-queue.md`.

If the queue is empty or contains only current-conversation entries, skip this step.

---

## Step 1 — Process distill queue

Read `_inbox/distill-queue.md`. If the file is missing or empty, tell the user and stop.

For each pending entry, one at a time:

a. Read the source conversation file referenced in the entry.
b. Draft the note content — structured, concise, suitable for `resources/`.
c. Show: proposed path, draft content, and a one-line reason for placing it there.
d. Engage interactively — the user may add context, redirect scope, change the path, or ask for revisions. Iterate until the user explicitly confirms or skips the item.
e. On confirm: write the note (Edit if the file exists, Write if new). If a new file is created, add it to `dashboard.md`.
f. On skip: leave the entry in the queue unchanged.

---

## Step 2 — Clean up

Remove only the confirmed distill entries from `_inbox/distill-queue.md` using Edit. Skipped entries remain.

Briefly list what was written and what remains in each queue.
