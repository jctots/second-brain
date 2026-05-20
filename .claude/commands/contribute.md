Contribute framework improvements from this instance to the upstream repository (GitHub). Execute in order:

## Prerequisites — Remote setup

This skill assumes the following remote convention. Ask the user to confirm which applies before Step 4.

**With a private vault remote (Tier 2 or upstream owner):**
- `origin` = private vault (e.g. gitea)
- `upstream` = GitHub repo you push branches to (your fork, or jctots/second-brain if you have direct access)
- Push branch to: `upstream`

**Without a private vault remote (Tier 1 — GitHub fork only):**
- `origin` = your GitHub fork
- No `upstream` needed
- Push branch to: `origin`

In all cases, `main` is your local vault branch.

## Step 1 — Detect candidate files

Run: `git diff --name-only main upstream/main`

Filter out content paths — never contribute anything under:
- `personal/`, `professional/`, `public/` — **except** the second-brain-setup SE docs listed below
- `_self/`, `_daily/`, `_conversations/`, `_inbox/`

Also block these framework-path files — they exist in both repos but serve different purposes and must never be a straight copy:
- `.gitignore` — the upstream version includes content-blocking entries the private vault does not need; changes must be crafted manually per the upstream version, not copied from the vault
- `dashboard.md` — generated file containing personal project links; the upstream version is a blank starter
- `.obsidian/` and `.obsidian-mobile/` — personal Obsidian settings (vault layout, plugins, keybindings); never contributed regardless of content

**Allowed exceptions under `personal/projects/second-brain-setup/`** (second-brain-setup SE docs, not private content):
- `architecture.md`
- `requirements.md`
- `verification.md`

Still block from that folder: `_memory.md`, `index.md`, `CLAUDE.md`, `decisions/`, `roadmap.md` — these are instance-specific.

Present the remaining files as a numbered list. For each file, flag with ⚠️ if it may contain instance-specific content — look for: hardcoded paths, personal names, short vault-specific aliases or abbreviations, email addresses, or employer names.

For each ⚠️ flagged file, show its diff against `upstream/main` inline so the user can verify no private content is included.

Ask the user to confirm the list, remove files, or cancel before proceeding. Do not continue until the user explicitly confirms.

## Step 2 — Review upstream decisions/ for staleness (conditional)

**Skip this step** if neither `architecture.md` nor `requirements.md` is in the confirmed file list.

If either is included: run `git show upstream/main:personal/projects/second-brain-setup/decisions/index.md`

Check whether the contributed changes to `architecture.md` or `requirements.md` conflict with or make stale any recent upstream decision (scan the index for the last 10–15 entries). Flag any stale entries with one line each. Ask the user whether to add a new decision before contributing.

- If yes: create a new `decisions/D{n}-{slug}.md` in your instance and add a row to `decisions/index.md` — these stay local and are not contributed.
- If no (or no stale entries): proceed.

## Step 3 — Branch name

Propose a branch name in the format `improve/short-description` derived from the changes. Ask the user to confirm or edit.

## Step 4 — Create branch and push to upstream

Run in sequence:
1. `git checkout -b {branch-name} {github-remote}/main` — start clean from upstream; use `upstream/main` (Tier 2 / owner) or `origin/main` (Tier 1)
2. `git checkout main -- {confirmed-files}` — bring in only the confirmed files from your vault's main
3. `git add {confirmed-files}`
4. `git commit -m "{short description of the improvement}"`
5. `git push {github-remote} {branch-name}` — use `upstream` (Tier 2 / owner) or `origin` (Tier 1)
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

## Step 6 — Delete local branch

Run: `git branch -D {branch-name}`

This is safe — the branch exists on GitHub until the PR is merged and deleted there. The local pointer is no longer needed.
