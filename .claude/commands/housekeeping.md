Housekeeping tasks that don't belong in a normal session. Execute these steps in order:

1. Scan `_conversations/` for files with an empty or missing `projects` frontmatter field. List them — do not infer or modify. These are candidates for manual tagging.

2. Scan `_inbox/` for files older than 14 days (compare `created` frontmatter or filename date against today). List them with their age — do not move or delete anything, just surface them for review.

3. Regenerate all indexes by running:
   - `python _scripts/index-conversations.py`
   - `python _scripts/update-project-indexes.py`

4. Check `_self/about.md` summary section (content above `<!-- extended -->`, or full file if no marker). Report character count and percentage of the 9,500-char limit. Then:
   - **Deduplication**: check for bullets that express the same trait from different angles — merge them in-place.
   - **Consolidation**: if `## Reflection` exceeds 20 bullets, group related bullets into labeled sub-clusters (e.g. `### Decision-making`, `### Tool and system thinking`).
   - **Budget**: if over 80% (7,600 chars), identify candidates for condensing or demotion to the extended section and offer to apply. Hard limit is 9,500 chars — flag as urgent if exceeded.
   - The extended section is evidence archive — never delete from it, only add to it.
   - Apply all changes only with confirmation. Always use Edit — never Write.

5. For each active project (any folder under `{personal,professional,public}/projects/` containing a `_memory.md`), check `CLAUDE.md` and `_memory.md` **separately** — each has its own 9,500-char limit. Report count and percentage for each file. If either exceeds 80% (7,600 chars), this is the time to clean up: identify candidates for demotion (lower-priority detail, superseded decisions, resolved questions) and offer to apply. Demotion options: move to extended section if it still has reference value, or delete if clearly stale. When adding a decision that supersedes a prior one, demote the prior in the same operation. Hard limit is 9,500 chars per file. Always use Edit — never Write — to preserve the extended section.

6. Briefly report: how many conversation files were classified, which were skipped and why, which inbox items need attention, whether the index regeneration succeeded, budget status of `_self/about.md` and each project file (flag any over 80% or over limit).
