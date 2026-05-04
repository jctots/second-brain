Save context from this conversation to persistent storage. Execute these steps in order:

1. Read `_inbox/memory-queue.md`. If missing or empty, fall back to a full retrospective scan of the current conversation for memory candidates, then continue from step 3.

2. Group queue entries by target file. For each target file:
   a. Read the current file.
   b. Consolidate all candidates targeting it — if entries conflict or suggest a reversal, use the context snippet to resolve; reload the source conversation only if the snippet is insufficient.
   c. Draft the minimal update: new bullets, edited entries, or section additions. Prefer editing existing entries over adding new ones.

3. Before writing, apply this filter: `_memory.md` captures current state, open questions, and active constraints — not implementation documentation. If a candidate describes *how something works* rather than *what has changed or what is still open*, skip it; that detail belongs in project documentation files. Write each update using Edit (never Write). If a target `_memory.md` doesn't exist, create it from template.

4. If new profile facts or behavioral observations exist, update `_self/about.md` — only add if not already captured. Behavioral corrections go to `_self/rules.md`.

4a. After all writes, run `python _tests/test_r6_hook_budget.py <project-path>` for the current project (e.g. `personal/projects/second-brain-setup`). `_self/` files are always included. Flag any file at WARN (≥80%) or FAIL (≥100%) — do not attempt to fix inline; flag for `/housekeeping`.

5. If an architectural decision was made, prepend an entry to `personal/projects/second-brain-setup/decisions.md`.

6. Remove processed entries from `_inbox/memory-queue.md` using Edit. Skipped or unresolved entries remain.

7. Briefly confirm what was written and what (if anything) remains in the queue.
