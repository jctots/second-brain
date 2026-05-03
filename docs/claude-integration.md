# 🤖 Claude Code Integration

> Session context is sent to Anthropic's API. Read [PRIVACY.md](../PRIVACY.md) before using Claude Code with sensitive content. For the local-first path, see [continue-integration.md](continue-integration.md).

How Claude Code fits into this second brain — hook architecture, slash commands, the context injection budget, and where judgment replaces automation.


## 🪝 Hook architecture

Claude Code supports hooks that execute shell commands at specific lifecycle events. This system uses two event types:

| Event | When it fires |
|---|---|
| `UserPromptSubmit` | Before Claude processes each user message |
| `Stop` | After Claude finishes a session |

### UserPromptSubmit hooks (context injection)

Four hooks fire on the first message of every conversation:

**`inject-profile.py`** — reads `_self/about.md` and prints its content to stdout. Claude Code captures this output and prepends it to Claude's context. This gives Claude a persistent profile and behavioral reflection about you, accumulated across sessions.

**`inject-rules.py`** — reads `_self/rules.md` and prints its content. This file holds feedback and behavioral corrections you've given the AI — it ensures corrections persist across sessions without having to repeat them.

**`inject-context-claude.py`** — detects which project you're working on by scanning your first message for folder names that match projects under `personal/`, `professional/`, or `public/projects/`. When it finds a match, it prints that project's `CLAUDE.md`.

**`inject-context-memory.py`** — same project-matching logic; prints that project's `_memory.md` (current state, open questions, key decisions).

Each hook is a separate entry in `.claude/settings.json` so each gets its own independent Claude Code output budget (see below).

### Stop hook (session saving)

**`save-conversation.py`** — saves the session transcript as a Markdown file in `_conversations/YYYY/MM/`. Adds YAML frontmatter (`title`, `session`, `context`, `projects`) for later indexing.


## 💰 Context injection budget

Claude Code caps all hook output at **10,000 characters per hook**. Content beyond that is silently truncated and replaced with a file reference — there's no warning, and Claude won't notice it happened.

The budget for this system:

| Hook | Script | Warn at | Hard limit |
|---|---|---|---|
| `UserPromptSubmit` #1 | `inject-profile.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #2 | `inject-rules.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #3 | `inject-context-claude.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #4 | `inject-context-memory.py` | 7,600 chars | 9,500 chars |

Each script has its own independent budget — splitting files into separate hooks gives each a full 9,500-char limit instead of sharing one budget. The warn threshold (80%) is enforced by `_tests/test_r6_hook_budget.py` in CI.

### The extended section pattern

`_memory.md` files may contain an `<!-- extended -->` marker. The inject scripts strip everything at and below this marker before printing — only content above the marker counts toward the budget.

```markdown
# _memory.md

## Current status
Active. Working on X.

## Key decisions
- Chose Y over Z because...

<!-- extended -->

## Archived decisions
- (older items demoted here by /sync-memory)
```

This lets you keep a single file with full context available on demand (read the file manually) while keeping the injected summary bounded. `/sync-memory` demotes lower-priority content below the marker rather than deleting it.

### Verifying hook health

At the start of every conversation, Claude should announce which files were loaded:

> *"Loaded: `personal/projects/my-project/CLAUDE.md` + `_memory.md`"*

No announcement = hook miss. This is the passive health check — you don't have to ask, and silence is observable.


## ⚡ Slash commands

Defined as Markdown files in `.claude/commands/`. Invoked by typing `/command-name` in a Claude Code session. Tab-completion lists available commands.

### /commit

**Purpose:** Draft a commit message from the staged diff and run git.

**How it works:**
1. Claude reads `git diff --cached` and proposes a commit message in the conversation
2. You confirm or edit the message
3. Claude calls `python _scripts/commit.py "your message"`, which handles `git pull --rebase` → `git commit` → `git push`

**Why split:** Message drafting requires judgment (what matters in this diff, what's the intent). Git mechanics are deterministic. Keeping AI in-conversation avoids spawning a cold-context agent just to run shell commands.

### /sync-memory

**Purpose:** Process `_inbox/memory-queue.md` into persistent files.

**How it works:**
1. Reads `_inbox/memory-queue.md` and groups entries by target file
2. For each target: reads the current file, consolidates candidates, writes the minimal update using Edit
3. Removes processed entries from the queue; skipped or unresolved entries remain
4. **Fallback:** if the queue is missing or empty, falls back to a full retrospective scan of the current conversation

**What it may update:**
- Project `_memory.md` — current status, key decisions, open questions (fixed sections, updated in-place)
- `_self/about.md` — new behavioral observations merged into existing bullets, never appended blindly
- `_self/rules.md` — behavioral corrections only, on explicit signal

**Scope:** Queue-driven. It doesn't scan prior sessions or rebuild indexes — that's `/housekeeping`.

### /distill

**Purpose:** Process `_inbox/distill-queue.md` into durable vault notes.

**How it works:** Interactive, one entry at a time:
1. Reads the source conversation referenced in each entry
2. Drafts note content — structured, concise, suitable for `areas/` or `resources/`
3. Presents the proposed path, draft content, and placement reason for your review
4. Iterates until you confirm or skip; on confirm, writes the note and updates `dashboard.md`
5. Removes only confirmed entries from the queue; skipped entries remain

**When to run:** When `_inbox/distill-queue.md` has pending items — typically after a conversation where Claude flagged items worth keeping as reference material.

### /housekeeping

**Purpose:** Maintenance sweep across all projects and conversations.

**What it does:**
- Scans `_conversations/` for files with empty `context` field; infers and backfills them
- Checks all `_memory.md` and `_self/about.md` files against size limits
- Offers to demote over-budget content below the `<!-- extended -->` marker
- Runs `update-project-indexes.py` to rebuild project `index.md` files

### /audit

**Purpose:** Check all active projects for structural completeness.

**What it checks:**
- Required files present: `CLAUDE.md`, `_memory.md`, `decisions.md`, `index.md`
- Required `_memory.md` sections present: `Current status`, `Key decisions`, `Open questions`
- `CLAUDE.md` has an "On sync memory" section
- Cross-pollination candidates (decisions in one project that could apply to another)

Report only — no auto-fixes.

### /review-memory

**Purpose:** Audit AI-maintained files for staleness and accuracy.

**What it reviews:** `_self/about.md`, all project `_memory.md` files, all `decisions.md` files.

**Not reviewed:** Project `CLAUDE.md` files — these are co-authored and reviewed when changed; they don't drift silently the way memory files do.


## ⚖️ The judgment / automation line

The system draws a deliberate line between what Claude does and what scripts do:

| Claude | Scripts |
|---|---|
| Commit message drafting | Git pull, commit, push |
| Project classification (which context/project) | Index file generation |
| Memory updates (what's worth keeping) | Frontmatter field updates |

**The rule:** if a step requires no judgment, it's a script. If it does, it's Claude.


## 🌱 How `_self/` files grow

**`_self/about.md`** — Claude maintains this across sessions via `/sync-memory`. Growth policy:

- New behavioral observations are **merged into existing bullets** rather than appended (if a bullet already covers the observation, it's updated in place)
- When the `## Reflection` section exceeds ~20 bullets, `/sync-memory` re-clusters them into labeled sub-groups

**`_self/rules.md`** — grows from corrections and confirmed preferences, not observations. Claude saves a rule when you correct an approach ("don't do X") or explicitly confirm a non-obvious one ("yes, keep doing that"). Each rule includes a `Why:` and `How to apply:` line so edge cases can be reasoned about, not just followed blindly. Rules are never appended automatically — they require an explicit signal from you.

The goal for both: the injected summary stays bounded and useful while remaining within the hook injection budget.


## 🔍 Project detection

`inject-context-claude.py` and `inject-context-memory.py` detect the current project by scanning the first user message for words that match folder names under `{personal,professional,public}/projects/`. The algorithm:

1. Read `hook_data["prompt"]` from the hook payload (the current message, available before it's written to the transcript)
2. Tokenize the message and compare against project folder names
3. On a match, `inject-context-claude.py` injects that project's `CLAUDE.md`; `inject-context-memory.py` injects its `_memory.md`

**Fallback:** If a project was mentioned but the hook missed it (typo, new project not yet created), the root `CLAUDE.md` instructs Claude to search manually and read the files.

**Multi-project sessions:** Mention all relevant projects in the first message — the hook matches all of them.


## 🔄 Continue.dev as a parallel path

Both paths can be active simultaneously — the line is yours to draw based on content sensitivity. For work involving personal or professional content, use Continue.dev + Ollama so nothing leaves your machine. See [continue-integration.md](continue-integration.md). Be aware that any file Claude Code reads is sent to Anthropic's API — read [PRIVACY.md](../PRIVACY.md).
