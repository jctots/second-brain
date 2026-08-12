# 🤖 Claude Code Integration

How Claude Code fits into this second brain — hook architecture, slash commands, the context injection budget, and where judgment replaces automation. For component interfaces and data flows, see [second-brain-setup/architecture.md](../personal/projects/second-brain-setup/architecture.md).

Claude Code is the AI interface at every deployment tier. For Tier 2/3 (private inference), set `ANTHROPIC_BASE_URL` to point at a LiteLLM gateway — the hooks and slash commands described here work identically regardless of where inference happens. **Requires Anthropic API key auth** (`ANTHROPIC_API_KEY` from console.anthropic.com) — incompatible with claude.ai subscription (OAuth). See [private-cloud-setup.md](private-cloud-setup.md) and [self-hosted-setup.md](self-hosted-setup.md).

> For Tier 1 (Anthropic API): session context is sent to Anthropic's servers. Read [PRIVACY.md](../PRIVACY.md) before using Claude Code with sensitive content.

## 🪝 Hook architecture

Claude Code supports hooks that execute shell commands at specific lifecycle events. This system uses `UserPromptSubmit` (before Claude processes a message) and `Stop`/`SessionEnd` (after Claude responds, for conversation saving).

| Hook                        | Event           | Injects                                                                                     | Tier     |
| --------------------------- | --------------- | ------------------------------------------------------------------------------------------- | -------- |
| `inject-context-claude.py`  | First message   | Detected project's `CLAUDE.md` — matched from project name in your first message            | Tier 1   |
| `inject-context-memory.py`  | First message   | Detected project's `_memory.md` — current state, open questions, key decisions              | Tier 1   |
| `inject-context-projects.py` | First message  | All active project paths + snapshot lines — vault-wide project registry                     | All      |
| `inject-context-project.py` *(planned)* | First message   | Same as above but detected via Qdrant embedding; falls back to keyword match                | Tier 2/3 |
| `inject-context-rag.py`     | Every turn      | Relevant note titles (Qdrant top-3); full content for 📖 markers from previous turn         | Tier 2/3 |
| `save-conversation.py`      | Stop/SessionEnd | Saves transcript to `_conversations/YYYY/MM/` with YAML frontmatter including event markers | All      |

For component interfaces and data flows, see [second-brain-setup/architecture.md — Claude Code interface](../personal/projects/second-brain-setup/architecture.md#claude-code-interface).

### Profile and corrections: `@` imports, not hooks

`_self/about.md` and `_self/corrections.md` are loaded by two `@` import lines at the top of the root `CLAUDE.md`:

```markdown
@_self/about.md
@_self/corrections.md
```

They are not hooks, and that difference matters in three ways:

- **No character cap.** Hook output is capped at 10,000 chars per invocation. Imports are not.
- **They survive `/compact`.** Hook output is a one-time injection into the first turn — after a compaction it is gone and does not come back. Imported files are part of the memory block and are re-sent every request.
- **Always loaded, not conditionally.** There is no first-turn detection and no project matching to miss.

The trade-off is that the content is in *every* request rather than just the first, so size is a running token cost instead of a one-off. `_tests/test_hook_budget.py` still measures both files and warns, but no longer fails the build on them.

A missing import is silently skipped by Claude Code — no warning, no error, and the session starts normally. So a fresh clone with an empty `_self/` works; it just has no profile loaded. `setup.py` seeds both files from `_templates/about-template.md` and `_templates/corrections-template.md` on first run.

### Active project registry

`inject-context-projects.py` injects a compact `## Active Projects` block on the first turn of every conversation. It scans `personal/`, `professional/`, and `public/projects/` and extracts the `## Snapshot` one-liner from each project's `_memory.md`. Projects without a snapshot are listed by path only.

This means Claude always knows what projects exist in your vault without you having to name them. New projects appear automatically the next conversation after their folder is created — no configuration needed.

**Budget:** ~60–80 chars per project; well within this hook's stdout cap for typical vault sizes.
**Tier:** All (no external dependencies — stdlib only).

### RAG failure notification

`inject-context-rag.py` distinguishes between two failure modes:

- **Not configured** (`OLLAMA_HOST` or `QDRANT_HOST` not set) — completely silent; intended for Tier 1 deployments where RAG services don't exist.
- **Configured but unavailable** (`URLError` when services are set) — emits a notification, because silence here means something broke.

When services are configured but unreachable:

| Event | What you see |
|---|---|
| First failure | Claude receives a ⚠️ warning line naming the failing service and address; relays it to you in that turn |
| Repeat failures (same session) | Silent — no warning per turn while services stay down |
| Recovery | Claude receives a ✅ line on the first turn services become reachable again, including the timestamp from when the outage started |

State is tracked in `.rag-status` in the vault root (gitignored). Format: `ok` or `error|TIMESTAMP|REASON` (pipe-delimited).

**Optional push notification:** Set `NTFY_URL` to your ntfy base URL in `.env`. The hook posts to `{NTFY_URL}/{RAG_NTFY_TOPIC}` on first failure and on recovery. `RAG_NTFY_TOPIC` defaults to `second-brain-rag` — override in `.env` if your ntfy instance uses a different naming scheme.

## 💰 Context injection budget

Claude Code caps a hook's output at **10,000 characters — per hook invocation, not per file.** One hook writes one stdout, so a turn that matches several projects puts every matched file under a single shared cap. Content beyond the cap is written to a file and replaced by a short preview, which drops the rest.

Each script gets its own independent cap, which is why the injectors are split into separate hook entries rather than one script. But splitting buys nothing *within* a script: `inject-context-memory.py` reading three projects' `_memory.md` still has one 10,000-char budget to spend across all three.

Two thresholds handle this, both set in `.env`:

| Variable | Default | Role |
|---|---|---|
| `HOOK_OUTPUT_CAP` | `9800` | **Runtime.** Sits just under the harness cap. Enforced inside the injectors |
| `HOOK_BUDGET_HARD` | `9000` | **Maintenance target.** Checked by CI. Headroom, not a hard stop |
| `HOOK_BUDGET_WARN_PCT` | `80` | Warn threshold as a percentage of `HOOK_BUDGET_HARD` |

A file may exceed `HOOK_BUDGET_HARD` and still inject fine. It is a signal to trim, not a failure of the mechanism.

| Hook                  | Script                     | Injects                                  |
| --------------------- | -------------------------- | ---------------------------------------- |
| `UserPromptSubmit` #1 | `inject-context-claude.py` | project `CLAUDE.md` — one per matched project |
| `UserPromptSubmit` #2 | `inject-context-memory.py` | project `_memory.md` — one per matched project |
| `UserPromptSubmit` #3 | `inject-context-rag.py`    | note titles (and 📖-flagged bodies)      |
| `UserPromptSubmit` #4 | `inject-context-projects.py` | one snapshot line per project           |

`_self/about.md` and `_self/corrections.md` are not in this table — they are `@` imports and carry no cap.

### What happens on overflow

Not silent truncation. `_hook_utils.emit_capped()` fills the budget with full file bodies and degrades whatever no longer fits to a one-line pointer telling Claude to read the file itself:

> _`_memory.md` for `my-project` did not fit the hook budget — read `personal/projects/my-project/_memory.md` before working on it._

So overflow costs you an extra read, and it is visible in the conversation. The `_self/` injectors do the same for a single oversized file, pointing at `/maintain` option 5.

### Budget enforcement

- **CI** — [`_tests/test_hook_budget.py`](../_tests/test_hook_budget.py) runs on every push to `main` and fails the build if any hook-injected file exceeds `HOOK_BUDGET_HARD` (default 9,000). The `_self/` imports are measured and warned on, but never fail the build.
- The test measures `len(label) + len(file)`, because each injector prepends a label line that also counts against the cap. A file measured alone can pass and still overflow live.
- The multi-project case is not enumerable in CI — that is what the runtime cap and `emit_capped()` cover.

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
3. Consolidates new content into existing sections in-place — merging with existing bullets where there is overlap, updating where a fact supersedes an existing one, adding only content with no existing home
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
- **Memory maintenance** — condense AI-maintained files that have grown large
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

**Purpose:** Query your vault by semantic similarity (Tier 2/3 only).

**How it works:**

Embeds the query via Ollama, searches Qdrant, returns top results ranked by similarity — file path, heading, and a short snippet per result. Prints "RAG not configured" or "RAG unavailable" if services are absent — no Tier 1 fallback.

**When to run:** Any time you want to surface related notes. Passive surfacing (hook-based) injects relevant note titles automatically each turn — `/search` is the active, on-demand complement. When Claude sees a title worth reading in full, it emits a `📖 [retrieve: path]` marker; the hook loads the full note on the next turn.

**Requires:** Qdrant running and vault indexed (`python _scripts/rag-embed.py`). `OLLAMA_HOST` and `QDRANT_HOST` must be set in `.env`.

## 🌱 How `_self/` files grow

**`_self/about.md`** — Claude maintains this across sessions via `/remember`. Growth policy:

- New behavioral observations are **merged into existing bullets** rather than appended (if a bullet already covers the observation, it's updated in place)
- When the `## Behavioral patterns` section exceeds ~20 bullets, `/maintain` option 4 re-clusters them into labeled sub-groups

**`_self/corrections.md`** — grows from corrections, confirmed preferences, and known failure modes. Claude saves an entry when you correct an approach ("don't do X") or explicitly confirm a non-obvious one ("yes, keep doing that"). Recurring failures (AI or user) are captured in the `## Known failure modes` section with root cause and prevention. Entries are never appended automatically — they require an explicit signal from you.

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
