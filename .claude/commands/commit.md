**Multi-root workspace:** If the user specifies a repo other than the default (e.g. "commit the public repo"), infer the full path from context. Use `git -C <path> diff --cached --stat` and `git -C <path> diff --cached` for the reads below, and pass `--repo <path>` to the script when running it.

Run `git diff --cached --stat` and `git diff --cached` to read the staged changes.

Analyze the changes and propose a commit message using this format:

**Type** — pick exactly one:
- `meta` — system changes: scripts, config, CLAUDE.md, settings, infra
- `note` — content changes: notes, daily entries, inbox, resources
- `project` — project-specific updates: memory, decisions, indexes
- `chore` — housekeeping: moves, renames, archiving, conversation logs

**Message format:**
```
{type}: {summary}

- bullet describing a significant change (omit section if changes are trivial)
- bullet describing another significant change
```

Rules: summary is imperative mood, ≤60 chars, no period.

Present the proposed message clearly and ask: "Confirm, edit, or cancel?"

Wait for the user's response.

- If they **confirm**: run the script using `-m` for the summary and `-b` for the body bullets joined with `\n`. Add `--no-pull` if the remote is already known to be in sync (e.g. a pull was just done manually). Example:
  ```
  python _scripts/commit.py -m "meta: migrate scripts to _scripts folder" -b "- add Python rewrites of PS1 scripts\n- add setup.sh and setup.ps1\n- remove .claude PS1 files"
  ```
- If they **edit**: use their version as the message, then run the script.
- If they **cancel**: stop without running anything.

**Handling rebase conflicts after the script runs:**

If the script fails with rebase conflicts, check the conflicted files with `git diff --name-only --diff-filter=U`. The most common cause is Gitea CI regenerating index files between your last pull and now. Resolve without analysis:

1. For any `index.md` file conflicted in `## files` or `## relevant conversations` — these are generated sections. Run:
   ```
   git checkout --ours <file>
   git add <file>
   ```
   Repeat for each conflicted index. Then `git rebase --continue` and `git push`.

2. For conflicts in any other file or section — stop and analyze before resolving.
