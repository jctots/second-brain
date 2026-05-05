# 🤖 Claude Code Integration

How Claude Code fits into this second brain — hook architecture, slash commands, the context injection budget, and where judgment replaces automation.

Claude Code is the AI interface at every deployment tier. For Tier 2/3 (private inference), set `ANTHROPIC_BASE_URL` to point at a LiteLLM gateway — the hooks and slash commands described here work identically regardless of where inference happens. See [private-cloud-setup.md](private-cloud-setup.md) and [self-hosted-setup.md](self-hosted-setup.md).

> For Tier 1 (Anthropic API): session context is sent to Anthropic's servers. Read [PRIVACY.md](../PRIVACY.md) before using Claude Code with sensitive content.


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

### /remember

**Purpose:** End-of-session retrospective — scan the current conversation for missed candidates, then process the memory queue.

**How it works:**
1. Scans the current conversation for missed distill candidates → appends to `_inbox/distill-queue.md`
2. Scans for missed memory candidates → appends to `_inbox/memory-queue.md`
3. Reads the memory queue, filters to current-conversation entries, groups by target file
4. Writes the minimal update to each target using Edit (never Write — preserves extended sections)
5. Removes processed entries; runs a budget check on any file written

**When to run:** At the end of any session with significant decisions or state changes.

### /distill

**Purpose:** Process pending queues into durable vault notes.

**How it works:** Two phases:
1. Reads `_inbox/memory-queue.md` for entries from *other* conversations (not current session) — processes and removes them without re-reading source conversations
2. Reads `_inbox/distill-queue.md` interactively, one entry at a time: reads source conversation, drafts note content, presents proposed path + draft for review; on confirm writes to `resources/` and updates `dashboard.md`; skipped entries remain

**When to run:** Periodically — when queues have accumulated entries from multiple sessions.

### /maintain

**Purpose:** Periodic vault health audit.

**What it checks:**
- Hook injection budgets — flags files approaching the 9,500-char limit
- PARA lifecycle — identifies notes that may be miscategorised
- Inbox aging — flags items sitting in `_inbox/` too long without processing
- Queue retrospective — checks for queue entries that reference deleted conversations

### /sync

**Purpose:** Git operations — commit staged work, check or pull framework updates.

**How it works:** Claude reads `git diff --cached`, proposes a commit message, you confirm or edit, then Claude calls `python _scripts/commit.py "message"` which handles `git pull --rebase` → `git commit` → `git push`.

**Why split:** Message drafting requires judgment. Git mechanics are deterministic. Keeping Claude in-conversation avoids spawning a cold-context agent to run shell commands.

### /contribute

**Purpose:** Contribute framework improvements from your instance to the upstream repository.

**What it does:** Packages framework-path changes (scripts, templates, workflows, commands) into a branch and opens a PR to the upstream GitHub repo. Content paths are never included.


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


## 🔒 Privacy and inference tiers

At Tier 1, any file Claude Code reads is sent to Anthropic's API — keep that boundary intentional. Read [PRIVACY.md](../PRIVACY.md).

At Tier 2/3, set `ANTHROPIC_BASE_URL` to a LiteLLM gateway pointing at Ollama. Claude Code's behaviour is identical — hooks fire, slash commands work, conversations are saved — but inference stays on user-controlled infrastructure. See [private-cloud-setup.md](private-cloud-setup.md) (VPS) or [self-hosted-setup.md](self-hosted-setup.md) (own hardware).
