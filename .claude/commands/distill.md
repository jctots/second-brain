Process distill events from the current conversation into durable vault notes, or extract portable concepts from a specified file. Two modes depending on invocation:

---

## Mode 1 — Conversation markers (no argument)

Invoked as `/distill`

1. **Scan for distill events** — look back through this conversation for 🗂️ `[distill event]` markers. If none found, tell the user and stop.

2. **Process each event, one at a time:**
   a. **Check for existing notes** — grep `resources/` across all contexts for notes with overlapping titles or tags. If a close match exists, read it and decide: propose updating the existing note instead of creating a new one.
   b. Draft the note content — structured, concise, suitable for `resources/`.
   c. Show: proposed path (existing or new), draft content, and a one-line reason for placing it there.
   d. Engage interactively — the user may add context, redirect scope, change the path, or ask for revisions. Iterate until the user explicitly confirms or skips the item.
   e. On confirm: write the note (Edit if exists, Write if new). Track new files for the dashboard update.
   f. On skip: move to the next item.

3. **Update `dashboard.md`** — in a single edit, add wikilink entries for all newly created notes under their correct context/PARA sections.

4. **Emit processed marker** — output `📦 [distill processed]` on its own line.

5. Briefly confirm what was written and what was skipped.

---

## Mode 2 — File extraction (with file path argument)

Invoked as `/distill path/to/file.md`

Use when you want to mine an existing document for portable concepts worth keeping as standalone atomic notes in `resources/`.

1. **Read the specified file** in full.

2. **Skip already-distilled sections** — scan for lines matching `*→ Distilled: [[...]]` directly under a heading. Do not re-propose those sections.

3. **Make a judgment pass** — identify remaining sections that contain portable concepts: general patterns, mental models, design frameworks, technology assessments, architectural principles. Skip system-specific implementation details (config values, script names, instance-specific decisions) — those belong in the source file.

4. **For each candidate, one at a time:**
   a. **Check for existing notes** — grep `resources/` across all contexts for notes with overlapping titles or tags. If a close match exists, read it and decide: propose updating the existing note instead of creating a new one.
   b. Propose a path in `resources/` (personal or public depending on sensitivity; existing path if updating).
   c. Draft a self-contained atomic note — structured, readable without the source file.
   d. Show: proposed path, draft content, one-line reason. If updating an existing note, show a diff-style summary of what would change.
   e. Engage interactively — user may revise, redirect, or skip. Iterate until confirmed or skipped.
   f. On confirm: write the note (Edit if exists, Write if new), appending a visible source line at the end:
      ```
      ---
      *Source: [[wikilink-to-source-file]]*
      ```
      Edit the source file: insert `*→ Distilled: [[path/to/note]]*` on the line immediately after the section heading. Track new notes for the dashboard update.
   f. On skip: move to the next candidate.

5. **Update `dashboard.md`** — in a single edit, add wikilink entries for all newly created notes under their correct context/PARA sections.

6. **Emit processed marker** — output `📦 [distill processed]` on its own line.

7. Briefly confirm what was written and what was skipped. The source file body is never modified beyond inserting the traceability line.
