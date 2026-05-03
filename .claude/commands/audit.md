Audit all active projects for structural completeness and cross-pollination opportunities. Execute these steps in order:

1. Find all active projects: scan `personal/projects/`, `professional/projects/`, and `public/projects/` for folders containing a `_memory.md`.

2. For each project, check:
   - Has all required files: `index.md`, `CLAUDE.md`, `_memory.md`?
   - `CLAUDE.md` contains an "On sync memory" section?
   - `_memory.md` uses fixed-sections-in-place pattern (Current status, Key decisions, Open questions) — not a growing append log?
   - Project has significant design history → has `decisions.md`?
   - Project has stable operational reference → has `reference.md`?

3. Scan for cross-pollination: note any pattern, convention, or file in one project that is absent in another and would be useful there.

4. Report results as a table:

| Project | Missing files | CLAUDE.md gaps | _memory.md pattern | Cross-pollination candidates |
|---|---|---|---|---|

List cross-pollination candidates separately below the table if there are any.

Do not fix anything. Report only.
