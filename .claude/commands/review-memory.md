Review all AI-maintained memory files for accuracy and currency. Execute these steps in order:

1. Find all AI-maintained vault memory files:
   - `_self/about.md`
   - `_self/rules.md`
   - For each active project (any folder under `personal/projects/`, `professional/projects/`, `public/projects/` containing a `_memory.md`): that project's `_memory.md` and `decisions.md` (if it exists)

2. For each file found:
   - Read the summary section only (content above `<!-- extended -->`, or full file if no marker)
   - Note the file's last-modified date
   - Flag with ⚠️ if last modified more than 30 days ago

3. Print each file's summary section in full, grouped by file, with a header showing path and last-modified date. Do not summarize or paraphrase — show the raw content so the user can read it directly.

4. After all files are shown, list any flagged files and invite the user to identify what needs updating. Do not make any edits — report only.

5. **Sanity check — workspace memory violations:** Locate the Claude workspace memory directory for this repo — it follows the pattern `~/.claude/projects/{encoded-repo-path}/memory/MEMORY.md`. Read `MEMORY.md`. If any files other than `MEMORY.md` exist in that directory, flag them with 🚨 — workspace memory is retired and new files there indicate the rule was not followed. List the filenames and their content so the user can decide whether to migrate or delete.
