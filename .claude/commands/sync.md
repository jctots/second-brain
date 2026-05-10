Git and framework operations.

**Optional argument:** pass `origin` or `upstream` to force the remote. If omitted, auto-detect: `upstream` present → use `upstream`; otherwise use `origin`.

Ask the user which operation:

**(1) commit** — commit staged work to the vault remote
**(2) check** — fetch framework remote and show what's available (no merge)
**(3) pull** — fetch and merge framework updates into the vault

---

## Option 1 — Commit

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

Present the proposed message and ask: "Confirm, edit, or cancel?"

- **Confirm**: run `python _scripts/commit.py -m "{summary}" -b "{bullets joined with \n}"`. Add `--no-pull` if the remote is already known to be in sync.
- **Edit**: use the user's version, then run the script.
- **Cancel**: stop without running anything.

**If the script fails with rebase conflicts**, check conflicted files with `git diff --name-only --diff-filter=U`:
1. For any `index.md` conflicted in `## files` or `## relevant conversations` — generated sections. Run `git checkout --ours <file> && git add <file>`. Repeat for each, then `git rebase --continue && git push`.
2. For conflicts in any other file or section — stop and analyze before resolving.

---

## Option 2 — Check for framework updates

1. Determine remote from argument or auto-detect.
2. Run `git fetch --prune {remote}`.
3. Run `git log HEAD..{remote}/main --oneline`. If empty, report "Already up to date." and stop.
4. Report how many commits are ahead and list them.

---

## Option 3 — Pull framework updates

1. Determine remote from argument or auto-detect.
2. Run `git fetch --prune {remote}`.
3. Run `git log HEAD..{remote}/main --oneline`. If empty, report "Already up to date." and stop.
4. Show framework-only changed files: `git diff --name-only HEAD {remote}/main`, filtered to exclude content paths (`personal/`, `professional/`, `public/`, `_self/`, `_daily/`, `_conversations/`, `_inbox/`).
5. Ask the user to confirm the merge before proceeding.
6. Run `git merge {remote}/main`. If there are conflicts, stop and list conflicted files — do not resolve automatically.
7. Run `git push origin main`.
8. Report: commits landed, framework files changed, push status.
