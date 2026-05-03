Contribute framework improvements from this instance to the upstream repository (GitHub). Execute in order:

## Step 1 — Detect candidate files

Run: `git diff --name-only main upstream/main`

Filter out content paths — never contribute anything under:
- `personal/`, `professional/`, `public/` — **except** the sbs SE docs listed below
- `_self/`, `_daily/`, `_conversations/`, `_inbox/`

**Allowed exceptions under `personal/projects/second-brain-setup/`** (second-brain-setup SE docs, not private content):
- `architecture.md`
- `requirements.md`

Still block from that folder: `_memory.md`, `index.md`, `CLAUDE.md`, `decisions.md`, `roadmap.md` — these are instance-specific.

Present the remaining files as a numbered list. For each file, flag with ⚠️ if it may contain instance-specific content — look for: hardcoded paths, personal names, short names (sb, sbg, sbs, sbc), email addresses, or employer names.

For each ⚠️ flagged file, show its diff against `upstream/main` inline so the user can verify no private content is included.

Ask the user to confirm the list, remove files, or cancel before proceeding. Do not continue until the user explicitly confirms.

## Step 2 — Review upstream decisions.md for staleness (conditional)

**Skip this step** if neither `architecture.md` nor `requirements.md` is in the confirmed file list.

If either is included: run `git show upstream/main:personal/projects/second-brain-setup/decisions.md`

Check whether the contributed changes to `architecture.md` or `requirements.md` conflict with or make stale any existing entry. Flag any stale entries with one line each. Ask the user whether to update `decisions.md` before contributing.

- If yes: update `personal/projects/second-brain-setup/decisions.md` in sb, then add it to the confirmed file list.
- If no (or no stale entries): proceed.

## Step 3 — Branch name

Propose a branch name in the format `improve/short-description` derived from the changes. Ask the user to confirm or edit.

## Step 4 — Create branch and push to upstream

Run in sequence:
1. `git checkout -b {branch-name} upstream/main` — start clean from upstream, not from sb
2. `git checkout main -- {confirmed-files}` — bring in only the confirmed files from sb's main
3. `git add {confirmed-files}`
4. `git commit -m "{short description of the improvement}"`
5. `git push upstream {branch-name}`
6. `git checkout main` — return to main

If step 1 fails because the branch already exists, stop and ask the user to choose a different name.

## Step 5 — Output PR content

Read `.github/PULL_REQUEST_TEMPLATE.md`. Fill it in based on the changes made. Output two clearly labelled copy-pastable blocks:

**PR Title:**
```
improve: {short description}
```

**PR Body:**
```
{filled template}
```

Then output the GitHub compare URL for the user to open the PR:
`https://github.com/{your-username}/second-brain/compare/{branch-name}?expand=1`

(Replace `{your-username}` with your GitHub username — upstream owner uses `jctots`, fork owners use their own.)
