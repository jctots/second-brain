Housekeeping tasks that don't belong in a normal session. Execute these steps in order:

1. Scan `_conversations/` for files with an empty or missing `projects` frontmatter field. List them — do not infer or modify. These are candidates for manual tagging.

2. Scan `_inbox/` for files older than 14 days (compare `created` frontmatter or filename date against today). List them with their age — do not move or delete anything, just surface them for review.

3. Run all scripts:
   - `python _scripts/index-conversations.py`
   - `python _scripts/update-project-indexes.py`
   - `python _tests/test_r6_hook_budget.py`

4. For `_self/about.md` and `_self/rules.md`, using the budget output from step 3:
   - **Deduplication**: check for bullets that express the same trait from different angles — merge them in-place.
   - **Consolidation**: if `## Reflection` in `about.md` exceeds 20 bullets, group related bullets into labeled sub-clusters (e.g. `### Decision-making`, `### Tool and system thinking`).
   - If either file is over 80%, identify candidates for condensing and offer to apply. Hard limit is 9,500 chars — flag as urgent if exceeded.
   - Apply all changes only with confirmation. Always use Edit — never Write.

5. For each active project (any folder under `{personal,professional,public}/projects/` containing a `_memory.md`), using the budget output from step 3: if `CLAUDE.md` or `_memory.md` exceeds 80% (7,600 chars), identify candidates for demotion (lower-priority detail, superseded decisions, resolved questions, implementation details already captured in other project files) and offer to apply. Demotion options: move to extended section if it still has reference value, or delete if clearly stale. Hard limit is 9,500 chars per file. Always use Edit — never Write — to preserve the extended section.

6. Review the 5 most recent conversations in `_conversations/` (by filename date) for missed distill and memory queue candidates — apply the same criteria as the during-conversation checks in root `CLAUDE.md`. For each candidate found: append to the appropriate queue file using Edit. List what was added (or "none found") in the final report.

7. Briefly report: how many conversation files were classified, which were skipped and why, which inbox items need attention, whether the index regeneration succeeded, budget status of `_self/about.md` and each project file (flag any over 80% or over limit), and what was added to the distill/memory queues in step 6.
