Save context from the current conversation to persistent storage. Execute in order:

1. **Scan current conversation for distill candidates** — identify patterns, tool comparisons, architectural concepts, or mental models with lasting reference value. Append new candidates to `_inbox/distill-queue.md` using Edit. Do not duplicate entries already in the queue.

2. **Scan current conversation for memory candidates** — identify project state changes, architectural decisions, profile facts, behavioral feedback. Append new candidates to `_inbox/memory-queue.md` using Edit. Do not duplicate entries already in the queue.

3. **Process memory queue entries from this conversation only** — read `_inbox/memory-queue.md`. Filter to entries whose `source:` references the current conversation. Do not load or process entries from other conversations — those are handled by `/distill`. For each target file among the filtered entries:
   a. Read the current file.
   b. Consolidate all candidates targeting it — if entries conflict or suggest a reversal, use the context snippet to resolve.
   c. Draft the minimal update: new bullets, edited entries, or section additions. Prefer editing existing entries over adding new ones.

4. **Apply the memory filter before writing:** `_memory.md` captures current state, open questions, and active constraints — not implementation documentation. If a candidate describes *how something works* rather than *what has changed or what is still open*, skip it. Write using Edit (never Write). If a target `_memory.md` doesn't exist, create it from template.

5. If new profile facts or behavioral observations exist, update `_self/about.md`. Behavioral corrections go to `_self/rules.md`. Only add if not already captured.

6. If any file was written in steps 4 or 5, run `python _tests/test_r6_hook_budget.py <project-path>` for the current project. `_self/` files are always included. Flag any file at WARN (≥80%) or FAIL (≥100%) — do not fix inline; flag for `/maintain`.

7. If an architectural decision about the vault was made this session, prepend an entry to `personal/projects/second-brain-setup/decisions.md`.

8. Remove processed entries from `_inbox/memory-queue.md` using Edit. Entries from other conversations remain untouched.

9. Briefly confirm what was written and what remains in the queue.
