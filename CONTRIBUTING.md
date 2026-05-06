# 🤝 Contributing

This is a personal project shared as a public template. Contributions are welcome in the form of bug reports, feature ideas, and documentation improvements.


## 🗂️ Repository layout

The root of this repository has three distinct groups:

```
_conversations/    ← framework: saved session transcripts
_daily/            ← framework: time-indexed daily notes
_inbox/            ← framework: capture zone
_infrastructure/   ← framework: stack manifest (stack.yaml) + Docker Compose for Tier 2/3
_scripts/          ← framework: automation and hook scripts
_self/             ← framework: AI-maintained profile files
_templates/        ← framework: note templates
_tests/            ← framework: script and hook budget tests
.claude/           ← framework: Claude Code hooks and slash commands
.obsidian/         ← framework: Obsidian config (workspace state gitignored)
.vscode/           ← framework: VS Code settings
personal/          ← content: private life, health, finances
professional/      ← content: career and current work
public/            ← content: open source, writing, learning
docs/              ← repo: documentation for contributors and users
.gitea/            ← repo: Gitea Actions CI workflows
.github/           ← repo: GitHub issue templates
CONTRIBUTING.md    ← repo: this file
LICENSE            ← repo: MIT license
PRIVACY.md         ← repo: data handling and privacy policy
README.md          ← repo: project overview
```

**Framework files** (`_*` and `.*`) are vault infrastructure — scripts, hooks, templates, and tool configuration.
**Content folders** are your PARA contexts — the actual notes live here.
**Repo files** exist for GitHub and contributors; they travel with the template but are not part of the note-taking workflow.

## 📖 Documentation levels

Three levels. Each has a distinct audience and purpose.

| Level | Files | Audience | Purpose |
|---|---|---|---|
| 1 | `README.md` | Anyone landing on the repo | Hook — what it is, why it exists, whether to keep reading |
| 2 | `docs/`, `CONTRIBUTING.md`, `PRIVACY.md` | Users and contributors | How to use it, set it up, and contribute |
| 3 | [`personal/projects/second-brain-setup/architecture.md`](personal/projects/second-brain-setup/architecture.md) | Implementers and forks | How it is built — components, interfaces, data flows |

### Change propagation

Framework files (`_scripts/`, `.claude/`, `_templates/`, `docs/`, `CONTRIBUTING.md`, etc.) travel to the upstream via `/contribute`. Two files from the sbs project also travel: `architecture.md` and `requirements.md`.

Everything else under `personal/projects/second-brain-setup/` (`_memory.md`, `CLAUDE.md`, `decisions.md`, `roadmap.md`, `index.md`) is instance-specific and never contributed upstream — `/contribute` blocks them explicitly.

**For fork instances contributing back:** `/contribute` works the same whether you are on Tier 1 (GitHub only) or Tier 2/3 (Gitea + GitHub fork) — the branch always starts fresh from the GitHub remote, so private vault content is never included. One UX note for Tier 1: the PR compare URL opens against your fork's `main` by default — switch the base repo to `jctots/second-brain` before submitting.

## 🔒 Your content stays local

The `.gitignore` blocks all content paths by default — `personal/**`, `professional/**`,
`public/**`, `_self/**`, `_daily/**`, `_inbox/**`, and `_conversations/**`. Only the PARA
skeleton (`.gitkeep` files) and the `second-brain-setup/` framework files are allowed through.
`git push` cannot accidentally publish your notes — the protection is structural, not
just conventional.

**When you fork:** your fork starts with this restrictive `.gitignore`. If you self-host
on Gitea and want content committed privately, update your fork's `.gitignore` to allow
those paths. The `.gitattributes` rule (`merge=ours` on `.gitignore`) ensures future
upstream merges will never overwrite your customization — your content policy stays yours.

**When contributing back:** your PR should only contain framework-path changes. Check
`git diff` before opening a PR — if anything under `personal/`, `professional/`, or
`public/` appears, do not include it.

**Additional safety net — `/contribute`:** If you use Claude Code, the `/contribute` slash command adds a second layer: it scans your changes, filters to framework-only paths, flags anything that looks like content, and prepares a PR description for review. It does not open a PR without your approval.

## 🔄 Getting upstream updates

This repo is a GitHub template. To pull in improvements from the upstream template after you've forked:

```bash
git remote add upstream https://github.com/jctots/second-brain.git
git fetch upstream
git merge upstream/main
```

Review the merge carefully — some files (`CLAUDE.md`, `personal/projects/second-brain-setup/`) are intentionally customized per user and should not be blindly overwritten.

## 🛠️ How to contribute

### Report a bug

Use the [bug report template](https://github.com/jctots/second-brain/issues/new?template=bug_report.md). Include:
- What you were trying to do
- What happened vs. what you expected
- Your OS, Python version, and VS Code / Claude Code version

### Suggest a feature

Use the [feature request template](https://github.com/jctots/second-brain/issues/new?template=feature_request.md). Include:
- The problem you're trying to solve
- What you'd like to see
- Any alternatives you've considered

### Improve the docs

Open an issue or submit a pull request directly. Documentation lives in `docs/` and `README.md`.


## 🔀 Pull requests

This repo is primarily a personal system — not all PRs will be merged, especially changes that reflect personal workflow preferences rather than general improvements. That said, PRs that fix bugs, improve portability, or reduce setup friction are welcome.

For significant changes, open an issue first to discuss before putting in the work.


## 🚫 What this project is not

- A general-purpose note-taking app
- A product with a support SLA
- Seeking feature parity with Obsidian, Notion, or similar tools

See the [comparison](README.md#️-how-this-compares) and [evolution](docs/evolution.md) for where this project is and isn't going.
