# 🤖 Claude Code Integration

How Claude Code fits into this second brain — hook architecture, slash commands, the context injection budget, and where judgment replaces automation.

Claude Code is the AI interface at every deployment tier. For Tier 2/3 (private inference), set `ANTHROPIC_BASE_URL` to point at a LiteLLM gateway — the hooks and slash commands described here work identically regardless of where inference happens. **Requires Anthropic API key auth** (`ANTHROPIC_API_KEY` from console.anthropic.com) — incompatible with claude.ai subscription (OAuth). See [private-cloud-setup.md](private-cloud-setup.md) and [self-hosted-setup.md](self-hosted-setup.md).

> For Tier 1 (Anthropic API): session context is sent to Anthropic's servers. Read [PRIVACY.md](../PRIVACY.md) before using Claude Code with sensitive content.


## 🪝 Hook architecture

Claude Code supports hooks that execute shell commands at specific lifecycle events. This system uses two event types:

| Event | When it fires |
|---|---|
| `UserPromptSubmit` | Before Claude processes each user message |
| `Stop` | After Claude finishes each response turn |
| `SessionEnd` | When the session closes |

### UserPromptSubmit hooks (context injection)

Four hooks fire on the first message of every conversation:

**`inject-profile.py`** — reads `_self/about.md` and prints its content to stdout. Claude Code captures this output and prepends it to Claude's context. This gives Claude a persistent profile and behavioral reflection about you, accumulated across sessions.

**`inject-rules.py`** — reads `_self/rules.md` and prints its content. This file holds feedback and behavioral corrections you've given the AI — it ensures corrections persist across sessions without having to repeat them.

**`inject-context-claude.py`** — detects which project you're working on by scanning your first message for folder names that match projects under `personal/`, `professional/`, or `public/projects/`. When it finds a match, it prints that project's `CLAUDE.md`.

**`inject-context-memory.py`** — same project-matching logic; prints that project's `_memory.md` (current state, open questions, key decisions).

Each hook is a separate entry in `.claude/settings.json` so each gets its own independent Claude Code output budget (see below).

### SessionEnd hook (session saving)

**`save-conversation.py`** — saves the session transcript as a Markdown file in `_conversations/YYYY/MM/`. Adds YAML frontmatter (`title`, `session`, `context`, `projects`) for later indexing.

The same script is also registered on `Stop` as a fallback — in case the session closes without a clean `SessionEnd` (e.g. process kill), the last response turn still saves the transcript.


## 💰 Context injection budget

Claude Code caps all hook output at **10,000 characters per hook**. Content beyond that is silently truncated and replaced with a file reference — there's no warning, and Claude won't notice it happened.

The budget for this system:

| Hook | Script | Warn at | Hard limit |
|---|---|---|---|
| `UserPromptSubmit` #1 | `inject-profile.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #2 | `inject-rules.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #3 | `inject-context-claude.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #4 | `inject-context-memory.py` | 7,600 chars | 9,500 chars |

Each script has its own independent budget — splitting files into separate hooks gives each a full 9,500-char limit instead of sharing one budget. The warn threshold (80%) is enforced by [`_tests/test_r6_hook_budget.py`](../_tests/test_r6_hook_budget.py) in CI.

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
- (older items demoted here by /remember)
```

This lets you keep a single file with full context available on demand (read the file manually) while keeping the injected summary bounded. `/remember` demotes lower-priority content below the marker rather than deleting it.

### Verifying hook health

At the start of every conversation, Claude should announce which files were loaded:

> *"Loaded: `personal/projects/my-project/CLAUDE.md` + `_memory.md`"*

No announcement = hook miss. This is the passive health check — you don't have to ask, and silence is observable.


## ⚡ Slash commands

Defined as Markdown files in `.claude/commands/`. Invoked by typing `/command-name` in a Claude Code session. Tab-completion lists available commands.

### /remember

**Purpose:** End-of-session processing — act on 🧠 memory and ✅ task markers emitted during the conversation.

**How it works:**
1. Scans the current conversation for 🧠 markers → routes each to the correct target file (`_memory.md`, `decisions.md`, `_self/about.md`, `_self/rules.md`)
2. Scans for ✅ markers → routes tasks to the project's `roadmap.md` or next-actions section
3. Writes updates using Edit (never Write — preserves extended sections)
4. Emits `🔁 [remember processed]` and `📋 [task processed]` markers, saved to conversation frontmatter

**When to run:** At the end of any session with significant decisions or state changes.

### /distill

**Purpose:** Process 🗂️ distill markers from the current conversation into durable vault notes.

**How it works:**
1. Scans the current conversation for 🗂️ markers
2. For each event: drafts note content, presents proposed path + draft for review; on confirm writes to `resources/` and updates `dashboard.md`; skipped entries move to the next
3. Emits `📦 [distill processed]` marker, saved to conversation frontmatter

**When to run:** Periodically — when distill events have accumulated in recent sessions.

### /maintain

**Purpose:** Periodic vault health audit — four options.

**What it covers:**
- **Generate artifacts** — run all scripts locally, same as CI
- **Pending events** — surface and process missed events from past conversations via `_conversations/pending-events.md`
- **Reports** — structural audit, PARA lifecycle, inbox aging, conversation frontmatter gaps
- **Reviews** — memory file staleness, `_self/` consolidation, budget management

### /sync

**Purpose:** Git operations — commit staged work, check or pull framework updates.

**How it works:** Claude reads `git diff --cached`, proposes a commit message, you confirm or edit, then Claude calls `python _scripts/commit.py "message"` which handles `git pull --rebase` → `git commit` → `git push`.

**Why split:** Message drafting requires judgment. Git mechanics are deterministic. Keeping Claude in-conversation avoids spawning a cold-context agent to run shell commands.

### /contribute

**Purpose:** Contribute framework improvements from your instance to the upstream repository.

**What it does:** Packages framework-path changes (scripts, templates, workflows, commands) into a branch and opens a PR to the upstream GitHub repo. Content paths are never included.

### /search

**Purpose:** Query your vault by meaning (Tier 2/3) or keyword (Tier 1).

**How it works:**
- **Tier 2/3 (semantic):** Embeds the query via Ollama, searches Qdrant, returns top results ranked by similarity — file path, heading, and a short snippet per result
- **Tier 1 (keyword):** Falls back to ripgrep across all vault `.md` files

**When to run:** Any time you want to surface related notes. Passive surfacing (hook-based) happens automatically at session start — `/search` is the active, on-demand complement.

**Requires:** Qdrant running and vault indexed (`python _scripts/embed-vault.py`) for semantic mode. Keyword mode has no additional requirements.


## ⚖️ The judgment / automation line

The system draws a deliberate line between what Claude does and what scripts do:

| Claude | Scripts |
|---|---|
| Commit message drafting | Git pull, commit, push |
| Project classification (which context/project) | Index file generation |
| Memory updates (what's worth keeping) | Frontmatter field updates |

**The rule:** if a step requires no judgment, it's a script. If it does, it's Claude.


## 🌱 How `_self/` files grow

**`_self/about.md`** — Claude maintains this across sessions via `/remember`. Growth policy:

- New behavioral observations are **merged into existing bullets** rather than appended (if a bullet already covers the observation, it's updated in place)
- When the `## Reflection` section exceeds ~20 bullets, `/remember` re-clusters them into labeled sub-groups

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
