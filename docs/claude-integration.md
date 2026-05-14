# 🤖 Claude Code Integration

How Claude Code fits into this second brain — hook architecture, slash commands, the context injection budget, and where judgment replaces automation. For component interfaces and data flows, see [second-brain-setup/architecture.md](../personal/projects/second-brain-setup/architecture.md).

Claude Code is the AI interface at every deployment tier. For Tier 2/3 (private inference), set `ANTHROPIC_BASE_URL` to point at a LiteLLM gateway — the hooks and slash commands described here work identically regardless of where inference happens. **Requires Anthropic API key auth** (`ANTHROPIC_API_KEY` from console.anthropic.com) — incompatible with claude.ai subscription (OAuth). See [private-cloud-setup.md](private-cloud-setup.md) and [self-hosted-setup.md](self-hosted-setup.md).

> For Tier 1 (Anthropic API): session context is sent to Anthropic's servers. Read [PRIVACY.md](../PRIVACY.md) before using Claude Code with sensitive content.

## 🪝 Hook architecture

Claude Code supports hooks that execute shell commands at specific lifecycle events. This system uses `UserPromptSubmit` (before Claude processes a message) and `Stop`/`SessionEnd` (after Claude responds, for conversation saving).

| Hook                        | Event           | Injects                                                                                     | Tier     |
| --------------------------- | --------------- | ------------------------------------------------------------------------------------------- | -------- |
| `inject-profile.py`         | First message   | `_self/about.md` — your profile and behavioral reflection                                   | All      |
| `inject-rules.py`           | First message   | `_self/rules.md` — feedback and corrections that persist across sessions                    | All      |
| `inject-context-claude.py`  | First message   | Detected project's `CLAUDE.md` — matched from project name in your first message            | Tier 1   |
| `inject-context-memory.py`  | First message   | Detected project's `_memory.md` — current state, open questions, key decisions              | Tier 1   |
| `inject-context-project.py` | First message   | Same as above but detected via Qdrant embedding; falls back to keyword match                | Tier 2/3 |
| `inject-context-rag.py`     | Every turn      | Relevant note titles (Qdrant top-3); full content for 📖 markers from previous turn         | Tier 2/3 |
| `save-conversation.py`      | Stop/SessionEnd | Saves transcript to `_conversations/YYYY/MM/` with YAML frontmatter including event markers | All      |

For component interfaces and data flows, see [second-brain-setup/architecture.md — Claude Code interface](../personal/projects/second-brain-setup/architecture.md#claude-code-interface).

## 💰 Context injection budget

Claude Code caps all hook output at **10,000 characters per hook**. Content beyond that is silently truncated and replaced with a file reference — there's no warning, and Claude won't notice it happened.

The budget for this system:

| Hook                  | Script                     | Warn at     | Hard limit   |
| --------------------- | -------------------------- | ----------- | ------------ |
| `UserPromptSubmit` #1 | `inject-profile.py`        | 8,000 chars | 10,000 chars |
| `UserPromptSubmit` #2 | `inject-rules.py`          | 8,000 chars | 10,000 chars |
| `UserPromptSubmit` #3 | `inject-context-claude.py` | 8,000 chars | 10,000 chars |
| `UserPromptSubmit` #4 | `inject-context-memory.py` | 8,000 chars | 10,000 chars |

Each script has its own independent budget — splitting files into separate hooks gives each a full 9,500-char limit instead of sharing one budget.

### Budget enforcement

The warn threshold (80%) is enforced in two places:

- **CI** — [`_tests/test_hook_budget.py`](../_tests/test_hook_budget.py) runs on every push to `main` and fails the build if any file exceeds 10,000 chars.
- **`/remember`** — step 7 of the `/remember` command runs `_tests/test_hook_budget.py` after writing context files and emits `⚠️ [budget warn]` for any file at or above the warn threshold.

### Verifying hook health

At the start of every conversation, Claude should announce which files were loaded:

> _"Loaded: `personal/projects/my-project/CLAUDE.md` + `_memory.md`"_

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

**Purpose:** End-of-session processing — persist what's worth keeping from the current conversation to project and profile files.

**How it works:**

1. Makes a judgment pass over the full conversation — markers are signals, not the authoritative source
2. Updates `## Quick status` in-place if project state changed materially
3. Appends a `<!-- remembered: YYYY-MM-DD -->` block to each target file using Edit (never Write)
4. Emits processed markers for what was actually written: `🔁 [remember processed]` (`_memory.md`), `🪪 [profile processed]` (`_self/`), `📋 [task processed]` (tasks)

**When to run:** At the end of any session with significant decisions or state changes.

### /distill

**Purpose:** Extract portable concepts into durable `resources/` notes. Two modes:

**Mode 1 — `/distill` (no argument):** Scans the current conversation for 🗂️ markers. For each event: checks for existing notes with overlapping titles or tags, drafts content, presents proposed path + draft for review, writes on confirm. Emits `📦 [distill processed]`.

**Mode 2 — `/distill path/to/file.md`:** Mines an existing document for portable concepts. Skips already-distilled sections (marked with `*→ Distilled: [[...]]*`). For each candidate: proposes a `resources/` path, drafts an atomic note, inserts a traceability line in the source file on confirm.

**When to run:** Periodically — when distill events have accumulated, or when a mature project/area doc has stable concepts worth extracting.

### /maintain

**Purpose:** Vault operations — seven options covering the full vault health cycle.

**What it covers:**

- **Generate artifacts** — run all scripts locally, same as CI: `generate-conversation-index.py`, `generate-project-indices.py`, `generate-dashboard.py`, `generate-pending-events.py`
- **Inbox processing** — route `_inbox/` items to the right PARA location; flag distill candidates
- **Event processing** — surface and process missed events from past conversations via `_conversations/pending-events.md`
- **Memory maintenance** — `_self/` consolidation and project `_memory.md` budget management
- **Resource note maintenance** — deduplicate and cross-link notes in `resources/`
- **Documentation maintenance** — consistency check across implementation, SE docs, and README
- **Reports** — structural audit, PARA lifecycle, inbox aging, conversation frontmatter gaps

### /sync

**Purpose:** Git operations — sync phone changes, commit desktop work, check or pull framework updates.

**Options:** `mobile` (merge origin/mobile → main, push both remotes), `commit` (mobile first, then commit staged changes, push both remotes), `check` (show available framework updates), `update` (merge framework updates).

**How it works:** Claude runs git commands directly — fetch, merge, diff, commit, push. Before any merge or commit, unstaged changes in CI-generated files (`_conversations/`, project `index.md` files) are discarded automatically. Commit message drafting requires judgment; git mechanics are deterministic.

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

## 🌱 How `_self/` files grow

**`_self/about.md`** — Claude maintains this across sessions via `/remember`. Growth policy:

- New behavioral observations are **merged into existing bullets** rather than appended (if a bullet already covers the observation, it's updated in place)
- When the `## Reflection` section exceeds ~20 bullets, `/remember` re-clusters them into labeled sub-groups

**`_self/rules.md`** — grows from corrections and confirmed preferences, not observations. Claude saves a rule when you correct an approach ("don't do X") or explicitly confirm a non-obvious one ("yes, keep doing that"). Each rule includes a `Why:` and `How to apply:` line so edge cases can be reasoned about, not just followed blindly. Rules are never appended automatically — they require an explicit signal from you.

The goal for both: the injected summary stays bounded and useful while remaining within the hook injection budget.

## 🔍 Project detection

**Tier 1 (keyword):** `inject-context-claude.py` and `inject-context-memory.py` detect the current project by scanning the first user message for words that match folder names under `{personal,professional,public}/projects/`. The algorithm:

1. Read `hook_data["prompt"]` from the hook payload (the current message, available before it's written to the transcript)
2. Tokenize the message and compare against project folder names
3. On a match, `inject-context-claude.py` injects that project's `CLAUDE.md`; `inject-context-memory.py` injects its `_memory.md`

**Tier 2/3 (semantic):** `inject-context-project.py` replaces the pair above. It embeds the first message via Ollama, queries Qdrant against project-indexed embeddings, and injects the matching project's `CLAUDE.md` + `_memory.md`. Falls back to keyword match when Qdrant is unreachable.

**Fallback (automated):** If no project is matched from the message, the hook reads the transcript for the most recently opened IDE file and infers the project from its path.

**Fallback (manual):** If the hook missed entirely (typo, new project not yet created), the root `CLAUDE.md` instructs Claude to search manually and read the files.

**Multi-project sessions:** Mention all relevant projects in the first message — the hook matches all of them.

## 🔒 Privacy and inference tiers

See [PRIVACY.md](../PRIVACY.md) for data handling at each tier. For how the LiteLLM gateway integrates at Tier 2/3, see [second-brain-setup/architecture.md — LiteLLM gateway interface](../personal/projects/second-brain-setup/architecture.md#litellm-gateway-interface).
