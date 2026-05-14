Git and framework operations.

**Optional argument:** pass `origin` or `upstream` to force the remote for options 3 and 4. If omitted, auto-detect: `upstream` present → use `upstream`; otherwise use `origin`.

Ask the user which operation:

**(1) mobile** — pull phone changes into main, push both remotes (ignores desktop staged changes)
**(2) commit** — commit desktop staged changes, merge mobile (if any), push both remotes
**(3) check** — fetch framework remote and show what's available (no merge)
**(4) update** — fetch and merge framework updates into the vault

---

## Shared: discard auto-updated unstaged files

Before any merge or commit step, run `git diff --name-only` to list unstaged files. For any file matching:
- `_conversations/index.md`
- `_conversations/pending-events.md`
- `personal/projects/*/index.md`, `professional/projects/*/index.md`, `public/projects/*/index.md`
- `dashboard.md`

Run `git checkout -- <file>` to discard. These are CI-generated — safe to discard.

If any other unstaged files remain after discarding, stop and warn the user — do not proceed.

---

## Option 1 — mobile

1. Discard auto-updated unstaged files (see above).
2. Run `git fetch origin`.
3. Run `git rev-parse --verify origin/mobile`. If it fails, report "origin/mobile does not exist — set up the mobile branch first." and stop.
4. Run `git log HEAD..origin/mobile --oneline`. If empty, report "Already up to date." and stop.
5. Run `git merge origin/mobile`. If there are conflicts, stop and list conflicted files — do not resolve automatically.
6. Run `git push origin`.
7. Report: commits merged from phone, push status for both remotes.

---

## Option 2 — commit

1. Discard auto-updated unstaged files (see above).
2. Run `git fetch origin`.
3. Run `git diff --cached --stat` and `git diff --cached` to read staged changes. If nothing is staged, stop and tell the user.
4. Analyze the changes and propose a commit message:

   **Type** — pick exactly one:
   - `meta` — system changes: scripts, config, CLAUDE.md, settings, infra
   - `note` — content changes: notes, daily entries, inbox, resources
   - `project` — project-specific updates: memory, decisions, indexes
   - `chore` — housekeeping: moves, renames, archiving, conversation logs

   **Message format:**
   ```
   {type}: {summary}

   - bullet describing a significant change (omit if changes are trivial)
   - bullet describing another significant change
   ```

   Rules: summary is imperative mood, ≤60 chars, no period.

5. Present the proposed message and ask: "Confirm, edit, or cancel?"
   - **Confirm / Edit**: write the full message to `.git/COMMIT_MSG_TMP`, run `git commit -F .git/COMMIT_MSG_TMP`, delete the temp file.
   - **Cancel**: stop without committing.
6. Run `git rev-parse --verify origin/mobile`. If it fails (branch does not exist), skip the merge. Otherwise run `git log HEAD..origin/mobile --oneline` — if empty, skip the merge; if not, run `git merge origin/mobile`. If there are conflicts, stop and list conflicted files — do not resolve automatically.
7. Run `git push origin`.
8. Report: commits merged from phone (if any), commit message used, push status for both remotes.

**If the push is rejected** (origin/main unexpectedly ahead): run `git pull --rebase origin main`, then `git push origin`. If rebase conflicts appear in `## files` or `## relevant conversations` sections of any `index.md`, run `git checkout --ours <file> && git add <file>` for each, then `git rebase --continue`. For conflicts in any other file — stop and analyze before resolving.

---

## Option 3 — check

1. Determine remote from argument or auto-detect.
2. Run `git fetch origin` then `git fetch --prune {remote}`.
3. Run `git diff --name-only origin/main {remote}/main`, filtered to exclude content paths (`personal/`, `professional/`, `public/`, `_self/`, `_daily/`, `_conversations/`, `_inbox/`). If empty, report "Already up to date." and stop.
4. Report the changed framework files. Tell the user to inspect the upstream branch in git graph before running `/sync update`.

---

## Option 4 — update

1. Determine remote from argument or auto-detect.
2. Run `git fetch --prune {remote}`.
3. Run `git log HEAD..{remote}/main --oneline`. If empty, report "Already up to date." and stop.
4. Show framework-only changed files: `git diff --name-only HEAD {remote}/main`, filtered to exclude content paths (`personal/`, `professional/`, `public/`, `_self/`, `_daily/`, `_conversations/`, `_inbox/`).
5. Ask the user to confirm the merge before proceeding.
6. Run `git merge {remote}/main`. If there are conflicts, stop and list conflicted files — do not resolve automatically.
7. Run `git push origin`.
8. Report: commits landed, framework files changed, push status for both remotes.
