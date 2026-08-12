---
context: personal
para: projects
created: 2026-04-29
---

# Second Brain — Architecture

[[second-brain-setup/index|⬅️ Project Index]]

> System structure: components, responsibilities, interfaces, and data flows.
>
> Related: `requirements.md` (constraints this satisfies) · `decisions/` (why it was built this way)

---

## Architecture principles

| # | Name | Summary | Location |
|---|---|---|---|
| A1 | Memory capture model | Vault-native; `/remember` judgment pass, consolidates in-place; markers as visual + backstop signal; `/maintain` for exceptional size maintenance | [§ A1](#a1--memory-capture-model) |
| A2 | Gitea Actions workflows | CI owns derived artifacts; local hooks only block bad commits | [§ A2](#a2--gitea-actions-workflows) |
| A3 | Hook guarantee | If a behavior must happen every session without fail, it needs a hook — instructions are not guaranteed | [§ Claude Code interface](#claude-code-interface) |
| A4 | RAG degrades to nothing | RAG is an enhancement, not a dependency — all invocation points exit cleanly when services are unavailable or unconfigured | [§ RAG pipeline](#rag-pipeline) |
| A5 | Optional services degrade gracefully | All optional services (Vikunja, ntfy, LiteLLM, RAG) configure via `.env` and fail silently when absent — core functionality works at Tier 1 without any of them | [§ Optional services](#optional-services) |

---

## Contents

- [Architecture principles](#architecture-principles)
- [System overview](#system-overview)
- [Components](#components)
  - [Vault](#vault)
  - [Foam / VSCode](#foam--vscode)
  - [Obsidian](#obsidian-desktop--mobile)
  - [Claude Code](#claude-code)
  - [Gitea Actions](#gitea-actions-ci)
  - [\_scripts/](#_scripts-shared-scripts)
- [Data flows](#data-flows)
- [Boundaries and ownership](#boundaries-and-ownership)
- [Claude Code interface](#claude-code-interface)
  - [Configuration surface](#configuration-surface)
  - [Hook events](#hook-events)
  - [Configured hooks](#configured-hooks)
  - [A1 — Memory capture model](#a1--memory-capture-model)
  - [A2 — Gitea Actions workflows](#a2--gitea-actions-workflows)
  - [CLAUDE.md](#claudemd)
  - [Auto-memory](#auto-memory)
  - [Slash commands](#slash-commands)
  - [Automation reliability summary](#automation-reliability-summary)
- [Optional services](#optional-services)
  - [Setup](#setup)
  - [Vikunja (task sync)](#vikunja-task-sync)
  - [ntfy (notifications)](#ntfy-notifications)
- [LiteLLM gateway interface](#litellm-gateway-interface)
  - [What it is](#what-it-is)
  - [Configuration](#configuration)
  - [Tier 2 — Private cloud](#tier-2--private-cloud-1)
  - [Tier 3 — Self-hosted](#tier-3--self-hosted-1)
  - [Feature degradation](#feature-degradation)
- [RAG pipeline](#rag-pipeline)
  - [Components](#rag-components)
  - [Data model](#data-model)
  - [Invocation points](#invocation-points)
  - [Graceful degradation](#graceful-degradation)
  - [Configuration](#rag-configuration)
- [Verification](#verification)
- [Key constraints satisfied](#key-constraints-satisfied)
- [Artifact ecosystem](#artifact-ecosystem)
  - [The artifacts](#the-artifacts)
  - [Framework vs. content split](#framework-vs-content-split)
  - [Deployment tiers](#deployment-tiers)
  - [Contribution workflow](#contribution-workflow)
  - [Documentation structure](#documentation-structure)

---

## System overview

A personal knowledge management system built on a git-backed Markdown vault. Three tools interact with the vault across two contexts (editing and reading). An AI layer (Claude Code) operates on the vault as a reasoning and automation tool, not as persistent infrastructure.

```
┌─────────────────────────────────────────────────────┐
│                      Vault                          │
│  (git repo — Gitea, private)                        │
│                                                     │
│  PARA × context structure                           │
│  personal/ · professional/ · public/                │
│  _inbox/ · _daily/ · _conversations/ · _self/       │
└──┬─────────────┬─────────────┬────────────────────────┘
   │             │             │
VSCode/Foam   Obsidian    Claude Code (AI agent)
(editing/   (reading/         │
 reading)    mobile)    ┌─────┴──────────────────────┐
                   Anthropic API         LiteLLM gateway
                   (cloud SaaS)         (Tier 2/3)
                                              │
                                  ┌───────────┴──────────┐
                            Remote Ollama/          Local Ollama
                            vLLM on VPS             (homelab)
                            (Tier 2)                (Tier 3)
   │ (git push)
   ├─────────────────────────────► Gitea Actions
   │                               (content CI: indexing, tests)
   └─────────────────────────────► GitHub Actions
                                   (framework CI: tests only)
```

---

## Components

### Vault

The single source of truth. All content lives here as plain Markdown files with YAML frontmatter.

**Structure:**
- `personal/` · `professional/` · `public/` — three contexts, each with PARA subdirectories
- `_inbox/` — capture zone, no context yet
- `_daily/` — time-indexed daily notes
- `_conversations/YYYY/MM/` — saved Claude Code session transcripts
- `_self/` — AI-maintained profile and behavioral reflection
- `_scripts/` — Python automation scripts (shared between hooks and CI)
- `.gitea/workflows/` — CI workflow definitions
- `.claude/` — Claude Code configuration (hooks, commands, auto-memory)

---

### Foam / VSCode

Primary editing environment. Resolves wikilinks, provides graph view, runs Claude Code via the extension.

**Owns:** editing, wikilink authoring, hook execution (hooks run in this process)
**Consumes:** vault files via filesystem; Claude Code hooks via `.claude/settings.json`
**Does not own:** reading/navigation UX (Obsidian is better for this)

---

### Obsidian (desktop + mobile)

Primary reading and navigation environment. Mobile access via obsidian-git plugin syncing to Gitea.

**Owns:** reading view, click-to-navigate, mobile capture
**Consumes:** vault files via filesystem (desktop) or git sync (mobile)
**Does not own:** editing at scale, hook execution, AI interaction

---

### Claude Code

AI reasoning layer. Operates on the vault as a tool-using agent: reads files, edits notes, runs scripts, manages project memory. Not persistent infrastructure — active only during a session.

**Owns:** session reasoning, memory management, slash command execution
**Consumes:** vault via filesystem tools; context via hook-injected files
**Does not own:** the vault (it assists, not governs); always-on processes

**Context loading (hook-guaranteed, every turn):**

`_self/about.md` and `_self/corrections.md` are not hook-injected — root `CLAUDE.md` loads them with `@` imports, which have no character cap and survive `/compact`.

```
UserPromptSubmit fires
  → inject-context-claude.py  → detects project, injects project CLAUDE.md  (first turn only)
  → inject-context-memory.py  → detects project, injects project _memory.md (first turn only)
  → inject-context-rag.py     → embeds message, queries Qdrant, injects matching note titles
                                 (every turn; silent if RAG unavailable)
```

---

### Gitea Actions (CI)

Deterministic automation that runs on push. Handles derived/generated artifacts that don't require judgment.

**Owns:** index regeneration, derived file updates
**Consumes:** vault via git clone; Python scripts from `_scripts/`
**Does not own:** content decisions, memory management, AI-assisted tasks

---

### `_scripts/` (shared scripts)

Python scripts callable both from Claude Code hooks and Gitea Actions CI. No external dependencies (stdlib only). Cross-platform (Windows + Linux/macOS via pathlib).

| Script | Called by | Purpose |
|---|---|---|
| `_hook_utils.py` | Shared library (imported by all hook scripts) | `is_first_turn`, `load_dotenv`, `get_first_user_message`, `get_ide_opened_file`, `find_project_from_file`, `strip_ide_selection`, `find_projects_in_message`, `CONTEXTS`. Not a hook itself — no stdin, no output. |
| `inject-context-claude.py` | Hook (`UserPromptSubmit`) | Detect project, inject project `CLAUDE.md` |
| `inject-context-memory.py` | Hook (`UserPromptSubmit`) | Detect project, inject project `_memory.md` |
| `inject-context-project.py` *(planned)* | Hook (`UserPromptSubmit`) | Detect project via Qdrant embedding (Tier 2/3) or keyword match (Tier 1 fallback); inject project `CLAUDE.md` + `_memory.md` — replaces `inject-context-claude.py` + `inject-context-memory.py` on Tier 2/3 |
| `inject-context-projects.py` | Hook (`UserPromptSubmit`) | Scan all active projects in `{personal,professional,public}/projects/`, extract `## Snapshot` from each `_memory.md`, inject compact `## Active Projects` registry. First turn only. No external dependencies. |
| `inject-context-rag.py` | Hook (`UserPromptSubmit`) | Embed user message via Ollama, query Qdrant top-3 above similarity threshold, inject matching note titles + file paths. Fires every turn. Degrades gracefully — exits 0 with no output when RAG is unconfigured or unreachable. |
| `save-conversation.py` | Hook (`Stop`, `SessionEnd`) | Save session transcript to `_conversations/`; scan for event markers; write `events`/`processed` frontmatter |
| `check-health.py` | Hook (`UserPromptSubmit`) | Check reachability of configured optional services (Ollama, Qdrant, Vikunja, Gitea, ntfy). First turn only. Silent on success; prints failures to conversation context. Reads `.env`. No external deps (stdlib only). |
| `generate-conversation-index.py` | CI (`generate-artifacts.yml`), `/maintain` | Regenerate `_conversations/index.md` |
| `generate-project-indices.py` | CI (`generate-artifacts.yml`), `/maintain` | Regenerate `## files`, `## relevant conversations`, and `## quick status` in each project `index.md` |
| `generate-dashboard.py` | CI (`generate-artifacts.yml`), `/maintain` | Regenerate `dashboard.md` — `## active projects` table (quick status) + context TOC (resources grouped by cluster tags) |
| `generate-pending-events.py` | CI (`generate-artifacts.yml`), `/maintain` | Scan conversations for unprocessed events; write `_conversations/pending-events.md` |
| `generate-pdf-sidecars.py` | CI (`generate-artifacts.yml`) | Generate Markdown sidecars for PDFs — text-layer via pdfplumber; image PDFs via tesseract OCR (external deps: pdfplumber, pypdfium2, pytesseract; installed via CI venv) |
| `rag-embed.py` | CI (`rag-embed-vault.yml`), manual | Walk vault, chunk by heading (H2/H3 with overlap), embed via Ollama (`embeddinggemma:latest`), upsert into Qdrant with metadata (path, para, context, project, tags). Supports `--files`/`--deleted` for incremental CI runs. |
| `rag-search.py` | `/search`, `/maintain` option 5 | Embed query string, query Qdrant, return top-5 ranked results (score · path · heading · snippet). Exits cleanly with a user-readable message when RAG is unconfigured or unreachable. |

---

## Data flows

### Session start

```
User types first message
  → UserPromptSubmit hook fires (guaranteed, every turn)
      inject-context-claude.py  → project CLAUDE.md → prepended to context       (first turn)
      inject-context-memory.py  → project _memory.md → prepended to context      (first turn)
      inject-context-projects.py → ## Active Projects registry (all projects)     (first turn)
      check-health.py           → service reachability check; prints failures     (first turn;
                                    silent if all services are healthy)
      inject-context-rag.py     → queries Qdrant, injects matching note titles   (every turn;
                                    silent if RAG unavailable)
  → Claude sees: hooks output + user message + root CLAUDE.md
```

### Session end

```
Claude finishes responding → Stop hook fires
  → save-conversation.py
      → writes _conversations/YYYY/MM/YYYY-MM-DD-{title}.md
      → scans assistant text for event markers (🧠 👤 🗂️ ✅) and processed markers (🔁 🪪 📦 📋)
      → writes events: [...] and processed: [...] to frontmatter
User pushes to Gitea
  → Gitea Actions triggers generate-artifacts.yml
      → generate-conversation-index.py regenerates _conversations/index.md
      → generate-project-indices.py updates project index.md files (## files, ## relevant conversations, ## quick status)
      → generate-dashboard.py regenerates dashboard.md (## active projects table + context TOC)
      → generate-pending-events.py writes _conversations/pending-events.md
      → CI commits results back to main
```

### Event marker model
*→ Distilled: [[personal/resources/ai-conversation-event-markers]]*

During a conversation, the AI emits inline markers when capture-worthy moments occur. Each marker includes a one-line description. `save-conversation.py` scans for these markers and writes two frontmatter fields:

- `events: [...]` — event types that occurred (`memory`, `distill`, `task`)
- `processed: [...]` — event types that were actioned (`remember`, `distill`, `task`)

**Markers emitted by AI:**

| Marker | Event type | Trigger |
|---|---|---|
| `🧠 [memory event]` | `memory` | Project state change, key decision, profile fact, behavioral observation |
| `👤 [profile event]` | `profile` | Profile fact or behavioral correction |
| `🗂️ [distill event]` | `distill` | Lasting reference value: technology analysis, tool comparisons, design patterns |
| `✅ [task event]` | `task` | Concrete next action for the user |
| `📖 [retrieve: path]` | — | Visual signal only — Claude reads the file directly when user confirms; no hook processing |

**Processed markers (emitted by slash commands):**

| Marker | Processed type | Emitted by |
|---|---|---|
| `🔁 [remember processed]` | `remember` | `/remember` |
| `🪪 [profile processed]` | `profile` | `/remember` (when profile events found) |
| `📦 [distill processed]` | `distill` | `/distill` |
| `📋 [task processed]` | `task` | `/remember` (when task events found) |

`_conversations/pending-events.md` (CI-generated) lists conversations where `events` has items not yet in `processed`. Used by `/maintain` as a backstop for missed sessions.

### `/remember` (user-triggered, end of session)

```
User runs /remember
  → scans current conversation for 🧠 markers
      → routes each to target file (_memory.md, decisions/, _self/about.md, _self/corrections.md)
      → writes using Edit (never Write)
  → scans current conversation for ✅ markers
      → routes tasks to project roadmap.md or _memory.md next actions
  → emits 🔁 [remember processed] (always)
  → emits 📋 [task processed] (if task events found)
```

### `/distill` (user-triggered, periodic)

```
User runs /distill
  → scans current conversation for 🗂️ markers
  → for each event:
      → drafts note content (structured, concise — resources/)
      → presents: proposed path + draft content + placement reason
      → iterates with user until confirmed or skipped
      → on confirm: writes note (Edit if exists, Write if new); updates dashboard.md
      → on skip: moves to next item
  → emits 📦 [distill processed]
```

---

## Boundaries and ownership

| Concern | Owner | Not owned by |
|---|---|---|
| Vault content | User + Claude (collaborative) | Any single tool |
| Wikilink format | Vault convention (R1, R7) | Any single tool |
| Hook execution | Claude Code harness | Claude (cannot self-trigger) |
| Index regeneration | Gitea Actions CI | Local hooks |
| Profile + memory | Claude (AI-maintained) | User (read, verify, correct) |
| Public sync | `/sync-public` command (judgment-driven) | CI (never automated) |

---

## Claude Code interface

How Claude's behavior in this repo is controlled — what is automated vs. instruction-dependent, and where each thing lives.

**A3 — Hook guarantee:** Hooks are guaranteed. Instructions are not. If a behavior must happen every session without fail, it needs a hook.

---

### Configuration surface

Three layers control Claude's behavior:

| Layer | File | Who enforces it |
|---|---|---|
| Hooks | `.claude/settings.json` | The harness — always runs, no Claude judgment |
| Instructions | `CLAUDE.md` (any level) | Claude — depends on compliance each turn |

---

### Hook events

| Event | When it fires | Common use |
|---|---|---|
| `UserPromptSubmit` | Before Claude sees the user's first message | Inject file content, prepend context |
| `PreToolUse` | Before any tool call | Guard, log, or block tool use |
| `PostToolUse` | After any tool call | Log results, trigger side effects |
| `Stop` | When Claude finishes responding | Save output, notify |
| `SessionEnd` | When the session closes | Final save, cleanup |

Hook commands receive JSON on stdin with fields including `transcript_path`, `cwd`, and the current message/tool context depending on event type.

---

### Configured hooks

#### Profile and corrections (`@` imports — not hooks)

**Files:** `_self/about.md`, `_self/corrections.md`
**Loaded by:** two `@` import lines at the top of root `CLAUDE.md`
**Why not hooks:** hook output is capped at 10,000 chars per invocation and is a one-time first-turn injection that does not return after `/compact`. Imports have no cap and are re-sent every request.
**Budget:** none enforced. `HOOK_BUDGET_HARD` is applied as an advisory warning only, because the content is in every request and size is a running token cost.
**Missing file:** silently skipped by Claude Code — no warning, no error. `setup.py` seeds both from `_templates/`.

---

#### Project CLAUDE.md injection (`UserPromptSubmit`)

**File:** `_scripts/inject-context-claude.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Reads `hook_data["prompt"]` (falls back to first user message in transcript). Scans `personal/`, `professional/`, `public/` for any project whose name appears in the message. For each matched project, reads its `CLAUDE.md`.
**Budget:** one `HOOK_OUTPUT_CAP` (9,800) shared across *all* matched projects; overflow degrades to a pointer line via `emit_capped()`. CI target `HOOK_BUDGET_HARD` (9,000) is per file, counting the injector's label.

---

#### Project _memory.md injection (`UserPromptSubmit`)

**File:** `_scripts/inject-context-memory.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Same project-matching logic as above. Reads `_memory.md` for each matched project.
**Budget:** same as above — one shared cap per invocation, not per project.

---

#### Conversation save (`Stop` + `SessionEnd`)

**File:** `_scripts/save-conversation.py`
**Fires on:** Both `Stop` and `SessionEnd`
**What it does:**
1. Reads the raw JSONL transcript from `transcript_path`
2. Parses `user`, `assistant`, and `ai-title` entries
3. Strips `<system-reminder>` blocks; formats `<ide_opened_file>` and `<ide_selection>` tags
4. Formats tool calls as compact blockquotes
5. Merges consecutive assistant segments
6. Scans assistant text for event markers (🧠 🗂️ ✅) and processed markers (🔁 📦 📋)
7. Writes to `_conversations/YYYY/MM/YYYY-MM-DD-{ai-title-as-slug}.md` with `events` and `processed` frontmatter fields

**Known behavior:** Fires on every `Stop` — partial conversations are saved incrementally and overwritten with the same filename.

---

#### RAG passive surfacing (`UserPromptSubmit`) — Tier 2/3

**File:** `_scripts/inject-context-rag.py`
**Fires on:** Every `UserPromptSubmit` (every turn)
**What it does:** Embeds the user's message via Ollama (`embeddinggemma:latest`); queries Qdrant for top-3 results above the similarity threshold (0.55); injects matching note titles + file paths as a `## Relevant vault notes` block. Claude reads files directly via its tools when the user confirms a suggested note.

**Degrades gracefully:** exits 0 with no output if hosts are unconfigured or services are unreachable.
**Budget:** output is titles only — typically a few lines; well within budget.
**Tier:** Tier 2/3 only — requires Qdrant and Ollama.

---

#### Project context injection via RAG (`UserPromptSubmit`) — Tier 2/3 *(planned)*

**File:** `_scripts/inject-context-project.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Embeds the user's first message via Ollama; queries Qdrant against project-indexed embeddings to identify the relevant project; injects its `CLAUDE.md` + `_memory.md`. Falls back to keyword match on project folder names when Qdrant is unavailable.
**Replaces:** `inject-context-claude.py` + `inject-context-memory.py` on Tier 2/3 (those scripts remain active for Tier 1).
**Budget:** shares the invocation's `HOOK_OUTPUT_CAP` with the other matched projects.
**Tier:** Tier 2/3 only.

---

#### Active project registry (`UserPromptSubmit`)

**File:** `_scripts/inject-context-projects.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Scans all `{personal,professional,public}/projects/*/` directories. For each project, reads the `## Snapshot` one-liner from `_memory.md` (if present). Injects a `## Active Projects` block listing every project path and its snapshot, giving Claude vault-wide project awareness at conversation start.
**Budget:** ~60–80 chars per project; well within limits for typical vault sizes.
**Tier:** All (no external dependencies).

---

### A1 — Memory capture model
*→ Distilled: [[personal/resources/ai-memory-capture-judgment-pass]]*

#### Design principle

Memory capture is vault-native — all captures land in versioned repo files readable in Obsidian/Foam, not in workspace-scoped side-channel storage. See [[second-brain-setup/decisions/D124-vault-native-memory-design-markers-judgment-pass-maintain-ba|D124]] for the full rationale vs. workspace memory.

#### Marker roles

Claude emits visual markers mid-conversation when it notices something worth capturing. Markers serve two purposes: visual signal for the user during the conversation, and detection signal for the `/maintain` backstop when `/remember` was not run.

| Marker | Meaning | Processing |
|---|---|---|
| 🧠 `[memory event]` | Project state, decision, open question | `/remember` (normal path) or `/maintain` backstop |
| ✅ `[task event]` | Concrete next action | Visual only — absorbed into 🧠 if worth persisting |
| 👤 `[profile event]` | Profile fact or behavioral correction | `/remember` inline (facts → `_self/about.md`, corrections → `_self/corrections.md`) or `/maintain` backstop |
| 🗂️ `[distill event]` | Lasting reference value beyond this project | `/distill` |
| 📖 `[retrieve: path]` | Vault note flagged as relevant by RAG surfacing | Visual signal only — Claude reads the file directly when user confirms; no hook processing |

#### `/remember` — judgment pass

At session end, `/remember` does a **judgment pass over the current conversation** — the full conversation is already in context, so this has no additional token cost. Claude extracts what's worth saving after the conversation has settled, avoiding intermediate states that may have been contradicted later in the session.

Output: new facts absorbed directly into the appropriate existing sections — merging with existing bullets where there is overlap, updating in-place where a fact supersedes an existing one. Never appends raw blocks.

`/remember` writes to project `_memory.md` always, and to `_self/about.md` or `_self/corrections.md` when 👤 profile content is present. It does not scan markers — the full conversation is the signal.

#### `/maintain` — backstop and consolidation

Two jobs:

**Backstop** — for past conversations where `/remember` was not run, `/maintain` scans 🧠 and 👤 markers. 🧠 markers are appended to `_memory.md`; 👤 markers are routed to `_self/about.md` or `_self/corrections.md` with judgment.

**Exceptional maintenance** — when files have grown large with genuine content over time, `/maintain` routes aging decisions to `decisions/`, stable reference to `/distill`, and targets ≤ 5,000 chars post-consolidation. Dropped items are intentional — working memory fades.

#### Missed capture coverage

| Failure | Mitigation |
|---|---|
| `/remember` not run | Markers → `/maintain` backstop |
| Marker not emitted | `/remember` judgment pass catches it |
| Both missed | Acceptable — requires two simultaneous failures |

---

### A2 — Gitea Actions workflows
*→ Distilled: [[personal/resources/ci-vs-local-hooks-design-principle]]*

**Design principle:** prefer CI for derived/generated artifacts; prefer local hooks only for things that must block a bad commit.

**Why two CI systems:** Gitea Actions runs on your private git host and has direct access to content paths (`_conversations/`, `_self/`, personal notes). GitHub Actions runs only on the public framework fork — it never has access to your content. This split is a privacy boundary, not just a technical preference. Content-aware workflows (indexing, budget tests on private files) must run on Gitea; framework tests run on either.

| Workflow | CI | Trigger | What it does |
|---|---|---|---|
| `generate-artifacts.yml` | Gitea Actions | Push to `main` | Runs generate scripts (conversation index, project indices, dashboard, pending events, PDF sidecars); commits updated artifacts |
| `perform-tests.yml` | Gitea Actions | Push to `main`, PR | Runs T1–T5 (all test files in `_tests/`) |
| `rag-embed-vault.yml` | Gitea Actions | Push to `main` (when `.md` files change) | Incrementally re-embeds changed vault files into Qdrant (Tier 2/3 only); skips cleanly if OLLAMA_HOST/QDRANT_HOST secrets not set |
| Framework tests | GitHub Actions | Push to public fork | Runs `_tests/` against framework files only |

---

### CLAUDE.md

**What CLAUDE.md is good for:**
- Structural rules (naming conventions, frontmatter, folder layout)
- Conditional behavior ("when working on a project, check for `_memory.md`")
- Tone and style guidance
- Workflow triggers tied to explicit user actions

**Reliability table — what is and isn't guaranteed at session start:**

| Behavior | Mechanism | Reliable? |
|---|---|---|
| Load `_self/about.md` | `@` import in root CLAUDE.md | Yes — every request, survives /compact |
| Load `_self/corrections.md` | `@` import in root CLAUDE.md | Yes — every request, survives /compact |
| Load project `CLAUDE.md` | Hook (`inject-context-claude.py`) | Yes — if project name is in first message |
| Load project `_memory.md` | Hook (`inject-context-memory.py`) | Yes — if project name is in first message |
| Infer context and confirm with user | CLAUDE.md instruction | No — can be missed |

**CLAUDE.md hierarchy:**

```
CLAUDE.md                                      ← root: system-wide rules
personal/projects/{project}/CLAUDE.md          ← project-specific rules
```

Context-level files (`personal/CLAUDE.md` etc.) were removed — rules folded into root CLAUDE.md as a table.

---

### Auto-memory

Workspace-scoped memory (`.claude/projects/.../memory/`) is **not used in this repo** (D94, D124). All persistent memory lives in vault files:

| File | Content | Loaded by |
|---|---|---|
| `_self/about.md` | Profile + behavioral patterns | `@` import in root CLAUDE.md |
| `_self/corrections.md` | Feedback rules and corrections | `@` import in root CLAUDE.md |
| project `_memory.md` | Project state + open questions | `inject-context-memory.py` |

These files travel with the repo, are git-versioned, and are readable in Obsidian. Workspace-scoped memory is machine-local, not vault-portable, and invisible to Obsidian/Foam — retired for these reasons. See [[second-brain-setup/decisions/D124-vault-native-memory-design-markers-judgment-pass-maintain-ba|D124]] for the full tradeoff analysis.

---

### Slash commands

Location: `.claude/commands/`

| Command | When to use |
|---|---|
| `/init` | Initialize a new vault entry — asks goal, inputs, and context; proposes PARA category + slug; creates project folder (4 files) or single area/resource file; updates dashboard |
| `/remember` | End of session — judgment pass over current conversation, consolidates new content into project `_memory.md` and `_self/` files in-place |
| `/distill` | Periodic — process 🗂️ event markers from current conversation into `resources/` notes |
| `/maintain` | Periodic vault operations — 7 options: generate artifacts, inbox processing, event processing, memory maintenance, resource note maintenance, documentation maintenance, reports |
| `/sync` | Git operations — commit staged work, check or pull framework updates |
| `/search` | Query vault by semantic similarity — calls `rag-search.py` (Ollama + Qdrant). Prints "RAG not configured" or "RAG unavailable" if services are absent; no Tier 1 fallback. |
| `/contribute` | Contribute framework improvements to upstream GitHub |

Adding a new command: create `.claude/commands/{name}.md`. No registration required. Avoid names that conflict with built-in Claude Code skills — built-ins take precedence on name collision.

---

### Automation reliability summary
*→ Distilled: [[personal/resources/ai-agent-hook-vs-instruction-reliability]]*

| Behavior | Mechanism | Reliability |
|---|---|---|
| Save conversation to `_conversations/` + ntfy if events pending | Hook (`Stop` + `SessionEnd`) | Guaranteed — ntfy skipped if `NTFY_URL` not set |
| Load `_self/about.md` | `@` import in root CLAUDE.md | Guaranteed — every request |
| Load `_self/corrections.md` | `@` import in root CLAUDE.md | Guaranteed — every request |
| Load project `CLAUDE.md` | Hook (`inject-context-claude.py`) | Guaranteed if project name in first message |
| Load project `_memory.md` | Hook (`inject-context-memory.py`) | Guaranteed if project name in first message |
| Emit event markers mid-conversation | CLAUDE.md instruction | Unreliable — mitigated by `/remember` judgment pass |
| Regenerate conversation + project indexes | Gitea Actions (`generate-artifacts.yml`) | Guaranteed on push to main |
| Generate `pending-events.md` | Gitea Actions (`generate-artifacts.yml`) | Guaranteed on push to main |
| Infer context and confirm with user | CLAUDE.md instruction | Unreliable |
| `/remember` trigger | User-invoked slash command | Reliable — user-triggered; session-scoped |
| `/distill` trigger | User-invoked slash command | Reliable — user-triggered; cross-session |
| `/maintain` trigger | User-invoked slash command | Reliable — user-triggered; periodic |
| RAG passive surfacing (Tier 2/3) | Hook (`inject-context-rag.py`, `UserPromptSubmit`) | Every turn; exits 0 with no output if Qdrant or Ollama is unreachable |
| Service health check (session start) | Hook (`check-health.py`, `UserPromptSubmit`) | Fires on first turn of every session; silent if all services are healthy |
| Project context injection via RAG (Tier 2/3) | Hook (`inject-context-project.py`, `UserPromptSubmit`) | Guaranteed first turn if Qdrant + Ollama reachable; keyword fallback to Tier 1 |

---

## Optional services

All optional services implement A5: configured via `.env` (written by `setup.py`), they degrade gracefully when absent or unreachable. Core vault functionality — editing, context injection, event capture, CI artifacts — works at Tier 1 without any optional service.

---

### Setup

`_scripts/setup.py` is the interactive configuration entry point. Run it once after cloning:

```
python _scripts/setup.py
```

Each service has a detection key (an env var in `.env`). If the key is already set, the service is shown as configured. Reconfigure any time by selecting it again.

| Service | Detection key | What it enables | Tier |
|---|---|---|---|
| RAG (Ollama + Qdrant) | `OLLAMA_HOST` | Semantic search, passive note surfacing | 2/3 |
| ntfy | `NTFY_URL` | Push notifications (CI failures, service health) | Any |
| Vikunja | `VIKUNJA_URL` | Task sync (`/remember` step 6, `/maintain` option 2) | Any |
| LiteLLM | — (manual) | Local LLM inference path | 2/3 |

---

### Vikunja (task sync)

**What it does:** `/remember` step 6 syncs `## Next Actions` from `_memory.md` to Vikunja (creates project and tasks if missing). `/maintain` option 2 pulls closed Vikunja tasks and removes matching entries from `## Next Actions`. Design principle: Vikunja is the source of truth; `_memory.md` is the cached display.

**Configuration:** `VIKUNJA_URL` (base URL, no `/api/v1`) + `VIKUNJA_TOKEN` (API token with unlimited scope). `setup.py` writes both to `.env` and creates `.mcp.json` at vault root (gitignored — contains the token). MCP package: `vikunja-mcp` (installed by `setup.py` via pip).

**Degradation:** if MCP is unavailable or Vikunja is unreachable, `/remember` and `/maintain` skip the sync step and report the failure.

---

### ntfy (notifications)

**What it does:** Push notifications to a self-hosted or hosted [ntfy](https://ntfy.sh) server. Two invocation points:

- `save-conversation.py` (Stop hook): after saving a session, sends a notification if the conversation has unprocessed events (events emitted but `/remember` not run).
- CI workflows (`generate-artifacts.yml`, `perform-tests.yml`, `rag-embed-vault.yml`): sends a notification on workflow failure.

Service health failures surface in the conversation via `check-health.py` (UserPromptSubmit hook, first turn) — not via ntfy, since the user is at the desktop.

**Configuration:** `NTFY_URL` (server base URL) + `NTFY_TOPIC` (topic name). CI uses the same topic via Gitea secrets (`NTFY_URL`, `NTFY_TOPIC`). HTTP `Title` header must be ASCII — emoji belong in the message body only.

**Degradation:** all callers wrap ntfy in `try/except Exception: pass` — if the server is unreachable or unconfigured, the notification is silently skipped and the calling action proceeds normally.

---

## LiteLLM gateway interface

How Claude Code connects to a local or private-cloud Ollama instance — the mechanism that enables Tier 2 and Tier 3 without switching tools or losing the harness.

---

### What it is
*→ Distilled: [[personal/resources/litellm-claude-code-local-model-proxy]]*

LiteLLM is a proxy that translates Claude Code's Anthropic Messages API format (`/v1/messages`) into the OpenAI-compatible format that Ollama exposes. Claude Code's harness — hooks, slash commands, conversation saving, context injection — continues to work unchanged. The only difference is where inference happens.

---

### Configuration

**Requires Anthropic API key auth.** `ANTHROPIC_BASE_URL` only works when authenticating via `ANTHROPIC_API_KEY` (from [console.anthropic.com](https://console.anthropic.com)). It is incompatible with claude.ai subscription (OAuth) — do not set these variables if you authenticate via `claude login`.

Two environment variables redirect Claude Code to the gateway:

```bash
export ANTHROPIC_API_KEY=sk-ant-...             # Anthropic Console API key
export ANTHROPIC_BASE_URL=http://localhost:4000  # LiteLLM endpoint
export ANTHROPIC_AUTH_TOKEN=sk-your-litellm-key  # LiteLLM key
```

Unset `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` (keep `ANTHROPIC_API_KEY`) to return to the Anthropic API directly. The harness is model-agnostic and unaffected by this switch.

---

### Model switching

With the gateway fixed, switch between Claude and local models using the `--model` flag — LiteLLM routes by model name to the backends defined in `_infrastructure/litellm_config.yaml`:

```bash
claude --model claude-sonnet-4-6   # routes to Anthropic via LiteLLM
claude --model llama3              # routes to local Ollama via LiteLLM
```

For a persistent default, add `"model": "claude-sonnet-4-6"` to `.claude/settings.local.json`.

---

### Tier 2 — Private cloud

LiteLLM runs on the same VPS as Ollama or vLLM. Set `ANTHROPIC_BASE_URL` to the VPS address with HTTPS and an API key. No local GPU required; inference stays on user-controlled infrastructure.

```
Claude Code → HTTPS → LiteLLM (VPS) → Ollama/vLLM (VPS)
```

---

### Tier 3 — Self-hosted

LiteLLM and Ollama run on user-owned hardware (same machine or private network). Set `ANTHROPIC_BASE_URL` to the address of the LiteLLM instance. No data leaves user-owned infrastructure.

```
Claude Code → LiteLLM (user-owned hardware) → Ollama (user-owned hardware)
```

---

### Feature degradation

Features that depend on Anthropic-specific model capabilities degrade when routing through a local model:

| Feature | Anthropic API | Local model via LiteLLM |
|---|---|---|
| Agentic tool use (multi-step edits) | Full | Degraded — depends on model quality |
| Extended thinking / effort levels | Available | Not available |
| Prompt caching | Available | Not available |
| Hooks + slash commands | Available | Available — harness is model-agnostic |
| Conversation saving | Available | Available — harness is model-agnostic |
| Context injection | Available | Available — harness is model-agnostic |

Use the local model path for sensitive-content queries and simple tasks. Complex agentic work benefits from the Anthropic API.

---

## RAG pipeline

Semantic search over vault content using Ollama embeddings and Qdrant vector storage. Tier 2/3 only — requires both services reachable. Implements A4: degrades to nothing when unavailable.

---

### RAG components

| Component | Role |
|---|---|
| `rag-embed.py` | Walk vault, chunk by heading (H2/H3 with sliding overlap windows), embed via Ollama, upsert into Qdrant. `--files`/`--deleted` args enable incremental CI runs. |
| `rag-search.py` | Embed query string via Ollama, query Qdrant top-5, return score · path · heading · snippet. |
| `rag-embed-vault.yml` | CI trigger: runs on push to `main` when `.md` files change; incremental by default (HEAD~1 diff); `workflow_dispatch` for full re-index. |

---

### Data model

Qdrant collection: `second_brain` — cosine similarity, 768-dim vectors (matching `embeddinggemma:latest`).

Each point:

| Field | Value |
|---|---|
| ID | Deterministic SHA-1 UUID from `file_path:heading:chunk_index` — prevents silent duplicates on re-index |
| Vector | 768-dim embedding from `embeddinggemma:latest` |
| `file_path` | Vault-relative path, forward-slash normalized |
| `heading` | H2/H3 heading text, or `__preamble__` |
| `para_category` | `projects`, `areas`, `resources`, or `archive` |
| `context` | `personal`, `professional`, or `public` |
| `project` | Project folder name if applicable |
| `tags` | Frontmatter tags |
| `snippet` | First 300 chars of chunk text |

Chunking: heading-based sections split at H2/H3 boundaries; sections > 1200 chars split into sliding windows (1200-char window, 200-char overlap). Sections < 50 chars skipped.

Exclusions: only files under `PARA_ROOTS = {"personal", "professional", "public"}` are indexed — everything else (`.git`, `.claude`, `_conversations`, `_tests`, `_scripts`, `_self`, `_daily`, etc.) is implicitly skipped. Within PARA_ROOTS: `SKIP_DIRS = {"tags"}`, `SKIP_FILES = {"index.md", "CLAUDE.md", "_memory.md"}`.

Note: deleting a file from the vault requires the `--deleted` flag on re-index — stale Qdrant points persist on re-upsert because Qdrant has no bulk-delete-by-source-file primitive. The CI workflow passes `--deleted` for files removed in the push.

---

### Invocation points

| Caller | Script | Behavior when RAG unavailable |
|---|---|---|
| `UserPromptSubmit` hook | `inject-context-rag.py` | Exits 0, no output — Claude sees nothing; no impact on conversation |
| `/search` | `rag-search.py` | Prints message, exits 0 — Claude relays it |
| `/maintain` option 5 | `rag-search.py` (once per resource note) | Prints message on first call, option aborts cleanly |
| CI `rag-embed-vault.yml` | `rag-embed.py` | Exits 0 if not configured; exits 1 if configured-but-down (red CI run alerts user) |

---

### Graceful degradation

A4: all invocation points produce a user-readable message rather than a Python traceback.

| Scenario | Detection | `rag-search.py` | `rag-embed.py` | CI |
|---|---|---|---|---|
| Not configured | `OLLAMA_HOST` or `QDRANT_HOST` env var is empty | Prints "RAG not configured", exits 0 | Prints "RAG not configured — skipping", exits 0 | Step exits 0 (green) |
| Ollama unreachable | `URLError` on embed call | Prints "RAG unavailable — Ollama unreachable: ...", exits 0 | All chunks warn, 0 upserted → prints error, exits 1 | Step exits 1 (red) |
| Qdrant unreachable | `URLError` on `ensure_collection` or search | Prints "RAG unavailable — Qdrant unreachable: ...", exits 0 | `ensure_collection` fails → prints error, exits 1 | Step exits 1 (red) |
| Partial chunk failures | `Exception` on some embed calls mid-run | N/A | Warns per chunk, continues; exits 0 if any chunks succeeded | Step exits 0 (green) |

**Why different exit codes between search and embed when services are down:** `rag-search.py` exits 0 so `/search` and `/maintain` receive a readable message Claude can relay. `rag-embed.py` exits 1 when configured-but-down so CI fails and alerts that incremental embedding was skipped.

**Why different exit codes between not-configured and down on embed:** not-configured is expected on Tier 1 and Tier 2/3 instances without RAG — a red CI run there would be noise on every push. Configured-but-down is unexpected and worth a CI alert.

**Ollama-down detection:** if all embed attempts fail (`embed_failures > 0 and total_chunks == 0`), the script exits 1. Partial failures (some chunks succeed) exit 0 — transient per-chunk errors are treated as acceptable degradation.

**Configuration source:** hosts (`OLLAMA_HOST`, `QDRANT_HOST`) have no Python-level fallback default — they must come from `.env` or a real env var. Ports (`OLLAMA_PORT`, `QDRANT_PORT`) default to standard values (11434, 6333). Any instance without `.env` entries for the hosts correctly hits the "not configured" path rather than attempting a connection to an arbitrary IP. On Gitea Actions, missing secrets evaluate to empty strings — also caught by the empty-host check.

---

### RAG configuration

Environment variables — loaded from `.env` at vault root (gitignored), or injected as CI secrets.

| Variable | Default | Notes |
|---|---|---|
| `OLLAMA_HOST` | (none — RAG disabled if empty) | Ollama hostname or IP |
| `OLLAMA_PORT` | `11434` | |
| `OLLAMA_API_KEY` | (none) | Optional — home lab threat model has no key |
| `QDRANT_HOST` | (none — RAG disabled if empty) | Qdrant hostname or IP |
| `QDRANT_PORT` | `6333` | |
| `QDRANT_API_KEY` | (none) | Optional |
| `RAG_COLLECTION` | `second_brain` | Qdrant collection name |
| `RAG_EMBED_MODEL` | `embeddinggemma:latest` | Ollama model used for embedding |
| `RAG_QUERY_LIMIT` | `10` | Raw results fetched from Qdrant before filtering |
| `RAG_MAX_FILES` | `3` | Max titles injected per turn |
| `RAG_SCORE_THRESHOLD` | `0.30` | Minimum similarity score to include a result |
| `RAG_TIMEOUT` | `5` | Seconds before Ollama/Qdrant requests time out |

`.env.example` at vault root documents the expected variables. `.env` is gitignored — never committed.

---

## Verification

Test scripts in `_tests/` verify requirements automatically. They run in Gitea Actions on every push to `main` (`.gitea/workflows/perform-tests.yml`). Each script is named after the requirement it covers.

| Test | Requirement | What it checks |
|---|---|---|
| `test_hook_budget.py` | R6 | Each hook-injected file, label included: warn at `HOOK_BUDGET_WARN_PCT` of `HOOK_BUDGET_HARD` (default 80% of 9,000), fail above it. `_self/` imports are measured but never fail |
| `test_inject_hooks.py` | R11 | Inject hook scripts — turn-detection, project matching, file injection, resilience |
| `test_save_conversation.py` | R10, R11 | Event marker extraction, conversation file writing, frontmatter |
| `test_generate_pending_events.py` | R7, R10, R11 | Pending events generation — frontmatter parsing, output format, resilience |
| `test_generate_dashboard.py` | R7, R11 | Dashboard generation — resource collection, quick status parsing, tag pages |
| `test_rag_embed.py` | R12 | `rag-embed.py` — point ID stability, skip logic, chunking contracts, graceful degradation |
| `test_rag_search.py` | R12 | `rag-search.py` — graceful degradation (not configured, services down, happy path) |
| `test_inject_context_rag.py` | R11, R12 | `inject-context-rag.py` — H1 extraction, graceful degradation, threshold filtering, deduplication, output format |

Tests are deterministic pass/fail scripts — stdlib Python only (R2), no Claude session required. When a test fails, CI blocks. Add a new test whenever a requirement becomes mechanically checkable.

---

## Key constraints satisfied

| Requirement | How |
|---|---|
| R1 — Obsidian + Foam | Static markdown, shortest-unique-path wikilinks, no plugin-dependent features |
| R2 — Platform portability | Python stdlib scripts, pathlib, no OS-specific calls |
| R3 — Reproducibility | `infra.yaml` + setup scripts; CI uses direct `run:` steps |
| R4 — Privacy | Three inference paths: cloud SaaS (Anthropic API, conscious tradeoff), private cloud (Claude Code + LiteLLM gateway → Ollama/vLLM on rented VPS), self-hosted (Claude Code + LiteLLM gateway → Ollama on user-owned hardware, no data leaves user infrastructure) |
| R5 — No always-on processes | CI for scheduled work; no background daemons |
| R6 — Hook budget | Two threshold vars (D134): `HOOK_OUTPUT_CAP` at runtime, `HOOK_BUDGET_HARD` in CI. Each hook script has its own 10,000-char stdout cap; `emit_capped()` degrades multi-project overflow to a pointer line. `_self/` files bypass the cap entirely as `@` imports |
| R7 — Static generated files | CI-owned indexes; no Dataview or plugin-dependent queries |

---

## Artifact ecosystem

This second brain spans three artifacts.

### The artifacts

| Artifact | Host | What it is |
|---|---|---|
| second-brain (upstream) | Public GitHub | Framework only — upstream template for all instances |
| second-brain (your instance) | Private git | Your working instance — framework + content |
| second-brain-setup | Project inside your instance | Meta-project — describes and maintains the system |

A community fork is any other instance — structurally identical to your instance, using the same upstream.

### Framework vs. content split

**Framework paths** (public, flow to/from the upstream):
`_scripts/` · `_templates/` · `.claude/` · `_infrastructure/` · `_tests/` · root `CLAUDE.md`
Plus: second-brain-setup SE docs (`personal/projects/second-brain-setup/` excluding per-instance files)

**Content paths** (private, never leave your instance):
`personal/` · `professional/` · `_self/` · `_daily/` · `_conversations/` · `_inbox/`

### Deployment tiers
*→ Distilled: [[personal/resources/three-tier-deployment-privacy-model]]*

The system supports three deployment tiers, all built from the same upstream framework.

> GitHub (framework CI) and cloud SaaS AI remain available at all tiers — Tier 2 and Tier 3 add private paths, they don't remove the SaaS options.

| Tier | Name | Git hosting | AI inference | Hardware required |
|---|---|---|---|---|
| 1 | SaaS | GitHub | Cloud SaaS (e.g., Claude Code) | None |
| 2 | Private cloud | Gitea on VPS | Ollama/vLLM on VPS (HTTPS + API key) | None (VPS subscription) |
| 3 | Self-hosted | Gitea on user-owned hardware | Ollama on user-owned hardware | Own hardware + GPU |

**Tier 1 — SaaS**

Framework: GitHub fork of the upstream. Content hosting: GitHub private fork. CI: GitHub Actions (framework tests only).

Privacy caveats: content is visible to cloud AI; content lives on GitHub. Not suitable for comprehensive capture of sensitive personal content. Use for: evaluating the framework, learning the design, contributing to the upstream.

**Tier 2 — Private cloud**

Framework: GitHub fork of the upstream (framework CI). Content hosting: Gitea on VPS. AI: Claude Code via LiteLLM gateway pointing to a remote Ollama or vLLM endpoint (HTTPS + API key) — no local GPU required. CI: Gitea Actions (content-aware: indexing, tests) + GitHub Actions (framework tests).

Privacy: content stays on user-controlled infrastructure; no local hardware beyond a laptop required.

**Tier 3 — Self-hosted**

Framework: GitHub fork of the upstream (framework CI). Content hosting: Gitea on user-owned hardware. AI: Claude Code via LiteLLM pointing to Ollama — both running on user-owned hardware (same machine or private network). No data leaves user-owned infrastructure. CI: Gitea Actions (content-aware: indexing, tests) + GitHub Actions (framework tests).

Privacy: content never leaves user-owned infrastructure. Full feature set, maximum sovereignty. Use for: a real second brain with comprehensive capture of personal, professional, and sensitive content.

The upgrade path (Tier 1 → Tier 2 → Tier 3) is documented in `docs/getting-started.md`.

### Contribution workflow

All instances use the same git workflow. The only mechanical difference is that the upstream repository owner pushes branches directly to the upstream; fork owners push to their own fork first.

| Task | Any instance |
|---|---|
| Use the framework | Works — always current via pull |
| Improve the framework | Push to branch → PR to upstream main |
| Pull framework improvements | `git fetch upstream && git merge` |
| Get docs updates | Flow downstream via merge |

The upstream improves from any contributor's workflow — no special publishing step, no stale snapshots.

#### Git remotes and branches

| Name | Tier 1 | Tier 2/3 | Used by |
|---|---|---|---|
| `origin` | GitHub fork | Private Gitea | All `/sync` options |
| `upstream` | — (origin IS the fork) | Public GitHub framework repo | `/sync check`, `/sync update`, `/contribute` |
| `origin/main` | Primary branch | Primary branch | All `/sync` options |
| `origin/mobile` | — (not applicable) | Phone branch — Obsidian mobile backups | `/sync mobile`, `/sync commit` |

On Tier 2/3, `origin` is configured to push `main` to both `origin/main` and `origin/mobile` via `remote.origin.push` refspecs, so `git push origin` always keeps both in sync. `/sync` commands depend on these conventions — do not rename the remotes or branches without updating the command instructions.

By convention:

```
# pull improvements
git fetch upstream
git merge upstream/main

# contribute improvement (fork owner)
git push origin improve/description
# open PR → upstream main on GitHub

# contribute improvement (upstream owner)
git push upstream HEAD:improve/description
# open PR → upstream main on GitHub
```

### Documentation structure
*→ Distilled: [[personal/resources/three-level-documentation-hierarchy]]*

Three levels. Each serves a different reader.

| Level | Files | Audience | Purpose |
|---|---|---|---|
| 1 | `README.md` | Anyone landing on the repo | Hook — what it is, why it exists, whether to keep reading |
| 2 | `docs/`, `CONTRIBUTING.md`, `PRIVACY.md` | Users and contributors | How to use it, set it up, and contribute |
| 3 | `architecture.md` (this file) | Implementers and forks | How it is built — components, interfaces, data flows |

**Where to write a given type of information:**

| Adding or changing... | Write here | Also update |
|---|---|---|
| What the system is / core behaviors | `README.md` § The solution | — |
| A new slash command | `README.md` slash commands table | `docs/claude-integration.md` (full description) |
| Setup steps | `docs/getting-started.md` | — |
| Hook or context injection behavior | `docs/claude-integration.md` | `architecture.md` if a component interface changes |
| Privacy / data handling | `PRIVACY.md` | — |
| Known limitations or roadmap | `docs/limitations-and-roadmap.md` | — |
| Deployment tier detail | `docs/getting-started.md` | `docs/private-cloud-setup.md` or `docs/self-hosted-setup.md` |
| Optional service setup or configuration | `docs/configuration.md` | `architecture.md` § Optional services |
| Repo layout or contribution workflow | `CONTRIBUTING.md` | — |
| System architecture or component interfaces | `architecture.md` (this file) | — |
| System requirements | `requirements.md` | — |
