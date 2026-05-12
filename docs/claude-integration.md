# 🤖 Claude Code Integration

How Claude Code fits into this second brain — hook architecture, slash commands, the context injection budget, and where judgment replaces automation. For component interfaces and data flows, see [second-brain-setup/architecture.md](../personal/projects/second-brain-setup/architecture.md).

Claude Code is the AI interface at every deployment tier. For Tier 2/3 (private inference), set `ANTHROPIC_BASE_URL` to point at a LiteLLM gateway — the hooks and slash commands described here work identically regardless of where inference happens. **Requires Anthropic API key auth** (`ANTHROPIC_API_KEY` from console.anthropic.com) — incompatible with claude.ai subscription (OAuth). See [private-cloud-setup.md](private-cloud-setup.md) and [self-hosted-setup.md](self-hosted-setup.md).

> For Tier 1 (Anthropic API): session context is sent to Anthropic's servers. Read [PRIVACY.md](../PRIVACY.md) before using Claude Code with sensitive content.


## 🪝 Hook architecture

Claude Code supports hooks that execute shell commands at specific lifecycle events. This system uses `UserPromptSubmit` (before Claude processes a message) and `Stop`/`SessionEnd` (after Claude responds, for conversation saving).

Four hooks fire on the first message of every conversation — each as a separate `.claude/settings.json` entry so each gets its own independent injection budget:

| Hook | Injects |
|---|---|
| `inject-profile.py` | `_self/about.md` — your profile and behavioral reflection |
| `inject-rules.py` | `_self/rules.md` — feedback and corrections that persist across sessions |
| `inject-context-claude.py` | Detected project's `CLAUDE.md` — matched from project name in your first message |
| `inject-context-memory.py` | Detected project's `_memory.md` — current state, open questions, key decisions |

`save-conversation.py` runs on `Stop`/`SessionEnd` — saves the session transcript to `_conversations/YYYY/MM/` with YAML frontmatter including event markers.

For component interfaces and data flows, see [second-brain-setup/architecture.md — Claude Code interface](../personal/projects/second-brain-setup/architecture.md#claude-code-interface).


## 💰 Context injection budget

Claude Code caps all hook output at **10,000 characters per hook**. Content beyond that is silently truncated and replaced with a file reference — there's no warning, and Claude won't notice it happened.

The budget for this system:

| Hook | Script | Warn at | Hard limit |
|---|---|---|---|
| `UserPromptSubmit` #1 | `inject-profile.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #2 | `inject-rules.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #3 | `inject-context-claude.py` | 7,600 chars | 9,500 chars |
| `UserPromptSubmit` #4 | `inject-context-memory.py` | 7,600 chars | 9,500 chars |

Each script has its own independent budget — splitting files into separate hooks gives each a full 9,500-char limit instead of sharing one budget.

### Budget enforcement

The warn threshold (80%) is enforced in two places:

- **CI** — [`_tests/test_hook_budget.py`](../_tests/test_hook_budget.py) runs on every push to `main` and fails the build if any file exceeds 10,000 chars.
- **`/remember`** — step 7 of the `/remember` command runs `_tests/test_hook_budget.py` after writing context files and emits `⚠️ [budget warn]` for any file at or above the warn threshold.

### The extended section pattern

`_memory.md` files may contain an `<!-- extended -->` marker — inject scripts strip everything at and below it, keeping the injected summary bounded while preserving full history in the file. `/remember` demotes lower-priority content below the marker rather than deleting it.

See [second-brain-setup/architecture.md — A1](../personal/projects/second-brain-setup/architecture.md#a1--extended-section-pattern) for the full pattern with example.

### Verifying hook health

At the start of every conversation, Claude should announce which files were loaded:

> *"Loaded: `personal/projects/my-project/CLAUDE.md` + `_memory.md`"*

No announcement = hook miss. This is the passive health check — you don't have to ask, and silence is observable.


## ⚡ Slash commands

Defined as Markdown files in `.claude/commands/`. Invoked by typing `/command-name` in a Claude Code session. Tab-completion lists available commands.

### /init

**Purpose:** Initialize a new vault entry — project, area, or resource.

**How it works:**
1. Asks three open questions in one message: your goal, your inputs (links, docs, a brief), and any other relevant context
2. Proposes a classification: PARA category (`projects`, `areas`, or `resources`), context (`personal`, `professional`, or `public`), a kebab-case slug, and a one-line description
3. Waits for your confirmation or adjustment before writing anything
4. Creates the entry: a 4-file project folder (`index.md`, `CLAUDE.md`, `_memory.md`, `reference.md`) for projects, or a single file for areas and resources
5. Updates `dashboard.md` with the new wikilink

**When to run:** Any time you start a new project, recognize a new ongoing responsibility, or want to capture a reference topic.

### /remember

**Purpose:** End-of-session processing — act on 🧠 memory and ✅ task markers emitted during the conversation.

**How it works:**
1. Scans the current conversation for 🧠 markers → routes each to the correct target file (`_memory.md`, `decisions/`, `_self/about.md`, `_self/rules.md`)
2. Scans for ✅ markers → routes tasks to the project's `roadmap.md` or next-actions section
3. Writes updates using Edit (never Write — preserves extended sections)
4. Emits `🔁 [remember processed]` and `📋 [task processed]` markers, saved to conversation frontmatter

**When to run:** At the end of any session with significant decisions or state changes.

### /distill

**Purpose:** Extract portable concepts into durable `resources/` notes. Two modes:

**Mode 1 — `/distill` (no argument):** Scans the current conversation for 🗂️ markers. For each event: checks for existing notes with overlapping titles or tags, drafts content, presents proposed path + draft for review, writes on confirm. Emits `📦 [distill processed]`.

**Mode 2 — `/distill path/to/file.md`:** Mines an existing document for portable concepts. Skips already-distilled sections (marked with `*→ Distilled: [[...]]*`). For each candidate: proposes a `resources/` path, drafts an atomic note, inserts a traceability line in the source file on confirm.

**When to run:** Periodically — when distill events have accumulated, or when a mature project/area doc has stable concepts worth extracting.

### /maintain

**Purpose:** Vault operations — six options covering the full vault health cycle.

**What it covers:**
- **Generate artifacts** — run all scripts locally, same as CI: `generate-conversation-index.py`, `generate-project-indices.py`, `generate-dashboard.py`, `generate-pending-events.py`
- **Inbox processing** — route `_inbox/` items to the right PARA location; flag distill candidates
- **Event processing** — surface and process missed events from past conversations via `_conversations/pending-events.md`
- **Memory maintenance** — `_self/` consolidation and project `_memory.md` budget management
- **Resource note maintenance** — deduplicate and cross-link notes in `resources/`
- **Reports** — structural audit, PARA lifecycle, inbox aging, conversation frontmatter gaps

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

**When to run:** Any time you want to surface related notes. Passive surfacing (hook-based) injects relevant note titles automatically each turn — `/search` is the active, on-demand complement. When Claude sees a title worth reading in full, it emits a `📖 [retrieve: path]` marker; the hook loads the full note on the next turn.

**Requires:** Qdrant running and vault indexed (`python _scripts/embed-vault.py`) for semantic mode. Keyword mode has no additional requirements.


## ⚖️ The judgment / automation line

If a step requires no judgment, it's a script. If it does, it's Claude. See [second-brain-setup/architecture.md — Boundaries and ownership](../personal/projects/second-brain-setup/architecture.md#boundaries-and-ownership) for the full breakdown.


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

See [PRIVACY.md](../PRIVACY.md) for data handling at each tier. For how the LiteLLM gateway integrates at Tier 2/3, see [second-brain-setup/architecture.md — LiteLLM gateway interface](../personal/projects/second-brain-setup/architecture.md#litellm-gateway-interface).
