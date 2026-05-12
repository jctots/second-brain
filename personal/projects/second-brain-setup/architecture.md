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
| A1 | Memory capture model | Vault-native; `/remember` judgment pass; markers as visual + backstop signal; `/maintain` consolidates | [§ A1](#a1--memory-capture-model) |
| A2 | Gitea Actions workflows | CI owns derived artifacts; local hooks only block bad commits | [§ A2](#a2--gitea-actions-workflows) |
| A3 | Hook guarantee | If a behavior must happen every session without fail, it needs a hook — instructions are not guaranteed | [§ Claude Code interface](#claude-code-interface) |

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
- [LiteLLM gateway interface](#litellm-gateway-interface)
  - [What it is](#what-it-is)
  - [Configuration](#configuration)
  - [Tier 2 — Private cloud](#tier-2--private-cloud-1)
  - [Tier 3 — Self-hosted](#tier-3--self-hosted-1)
  - [Feature degradation](#feature-degradation)
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

**Context loading at session start (hook-guaranteed):**

```
UserPromptSubmit fires
  → inject-profile.py         → injects _self/about.md summary
  → inject-rules.py           → injects _self/rules.md summary
  → inject-context-claude.py  → detects project, injects project CLAUDE.md
  → inject-context-memory.py  → detects project, injects project _memory.md
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
| `inject-profile.py` | Hook (`UserPromptSubmit`) | Inject `_self/about.md` summary |
| `inject-rules.py` | Hook (`UserPromptSubmit`) | Inject `_self/rules.md` summary |
| `inject-context-claude.py` | Hook (`UserPromptSubmit`) | Detect project, inject project `CLAUDE.md` |
| `inject-context-memory.py` | Hook (`UserPromptSubmit`) | Detect project, inject project `_memory.md` |
| `save-conversation.py` | Hook (`Stop`, `SessionEnd`) | Save session transcript to `_conversations/`; scan for event markers; write `events`/`processed` frontmatter |
| `generate-conversation-index.py` | CI (`generate-artifacts.yml`), `/maintain` | Regenerate `_conversations/index.md` |
| `generate-project-indices.py` | CI (`generate-artifacts.yml`), `/maintain` | Regenerate `## files`, `## relevant conversations`, and `## quick status` in each project `index.md` |
| `generate-dashboard.py` | CI (`generate-artifacts.yml`), `/maintain` | Regenerate `dashboard.md` — `## active projects` table (quick status) + context TOC (resources grouped by cluster tags) |
| `generate-pending-events.py` | CI (`generate-artifacts.yml`), `/maintain` | Scan conversations for unprocessed events; write `_conversations/pending-events.md` |
| `commit.py` | `/sync` (commit option) | Stage → commit → pull rebase → push |

---

## Data flows

### Session start

```
User opens VSCode → types first message
  → UserPromptSubmit hook fires (guaranteed)
      inject-profile.py         → _self/about.md → prepended to Claude's context
      inject-rules.py           → _self/rules.md → prepended to Claude's context
      inject-context-claude.py  → project CLAUDE.md → prepended to Claude's context
      inject-context-memory.py  → project _memory.md → prepended to Claude's context
  → Claude sees: hooks output + user message + root CLAUDE.md
```

### Session end

```
Claude finishes responding → Stop hook fires
  → save-conversation.py
      → writes _conversations/YYYY/MM/YYYY-MM-DD-{title}.md
      → scans assistant text for event markers (🧠 🗂️ ✅ 🔁 📦 📋)
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
| `🗂️ [distill event]` | `distill` | Lasting reference value: technology analysis, tool comparisons, design patterns |
| `✅ [task event]` | `task` | Concrete next action for the user |

**Processed markers (emitted by slash commands):**

| Marker | Processed type | Emitted by |
|---|---|---|
| `🔁 [remember processed]` | `remember` | `/remember` |
| `📦 [distill processed]` | `distill` | `/distill` |
| `📋 [task processed]` | `task` | `/remember` (when task events found) |

`_conversations/pending-events.md` (CI-generated) lists conversations where `events` has items not yet in `processed`. Used by `/maintain` as a backstop for missed sessions.

### `/remember` (user-triggered, end of session)

```
User runs /remember
  → scans current conversation for 🧠 markers
      → routes each to target file (_memory.md, decisions/, _self/about.md, _self/rules.md)
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

#### Profile injection (`UserPromptSubmit`)

**File:** `_scripts/inject-profile.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Reads `_self/about.md` and outputs the full file content.
**Budget:** ≤ 10,000 chars (warn at 8,000; consolidation target 5,000).

---

#### Project CLAUDE.md injection (`UserPromptSubmit`)

**File:** `_scripts/inject-context-claude.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Reads `hook_data["prompt"]` (falls back to first user message in transcript). Scans `personal/`, `professional/`, `public/` for any project whose name appears in the message. For each matched project, reads its `CLAUDE.md`.
**Budget:** ≤ 10,000 chars (warn at 8,000; consolidation target 5,000).

---

#### Project _memory.md injection (`UserPromptSubmit`)

**File:** `_scripts/inject-context-memory.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Same project-matching logic as above. Reads `_memory.md` for each matched project.
**Budget:** ≤ 10,000 chars (warn at 8,000; consolidation target 5,000).

---

#### Feedback injection (`UserPromptSubmit`)

**File:** `_scripts/inject-rules.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Reads `_self/rules.md` and outputs the full file content.
**Budget:** ≤ 10,000 chars (warn at 8,000; consolidation target 5,000).

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
| 👤 `[profile event]` | Profile fact or behavioral correction | `/remember` inline (facts → `_self/about.md`, corrections → `_self/rules.md`) or `/maintain` backstop |
| 🗂️ `[distill event]` | Lasting reference value beyond this project | `/distill` |

#### `/remember` — judgment pass

At session end, `/remember` does a **judgment pass over the current conversation** — the full conversation is already in context, so this has no additional token cost. Claude extracts what's worth saving after the conversation has settled, avoiding intermediate states that may have been contradicted later in the session.

Output: one appended block per target file. Always appends — never edits in-place.

```
<!-- remembered: YYYY-MM-DD -->
- [what was captured]
```

`/remember` writes to project `_memory.md` always, and to `_self/about.md` or `_self/rules.md` when 👤 profile content is present. All target files are append-only — never edits sections in-place. It does not scan markers — the full conversation is the signal.

#### `/maintain` — backstop and consolidation

Two jobs:

**Backstop** — for past conversations where `/remember` was not run, `/maintain` scans 🧠 and 👤 markers. 🧠 markers are appended to `_memory.md`; 👤 markers are routed to `_self/about.md` or `_self/rules.md` with judgment.

**Consolidation** — when `_memory.md` or `_self/` files exceed 8,000 chars, `/maintain` merges appended `<!-- remembered: -->` blocks into the structured sections, routes aging content to `decisions/` or drops it, and targets ≤ 5,000 chars post-consolidation. Dropped items are intentional — working memory fades.

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
| `generate-artifacts.yml` | Gitea Actions | Push to `main` | Runs `generate-conversation-index.py`, `generate-project-indices.py`, `generate-pending-events.py`; commits updated indexes and `pending-events.md` |
| `test.yml` | Gitea Actions | Push to `main` | Runs `test_hook_budget.py` |
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
| Load `_self/about.md` summary | Hook (`inject-profile.py`) | Yes — guaranteed first turn |
| Load `_self/rules.md` | Hook (`inject-rules.py`) | Yes — guaranteed first turn |
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

| File | Content | Injected by |
|---|---|---|
| `_self/about.md` | Profile + behavioral patterns | `inject-profile.py` |
| `_self/rules.md` | Feedback rules and corrections | `inject-rules.py` |
| project `_memory.md` | Project state + open questions | `inject-context-memory.py` |

These files travel with the repo, are git-versioned, and are readable in Obsidian. Workspace-scoped memory is machine-local, not vault-portable, and invisible to Obsidian/Foam — retired for these reasons. See [[second-brain-setup/decisions/D124-vault-native-memory-design-markers-judgment-pass-maintain-ba|D124]] for the full tradeoff analysis.

---

### Slash commands

Location: `.claude/commands/`

| Command | When to use |
|---|---|
| `/init` | Initialize a new vault entry — asks goal, inputs, and context; proposes PARA category + slug; creates project folder (4 files) or single area/resource file; updates dashboard |
| `/remember` | End of session — judgment pass over current conversation, appends captures to project `_memory.md` |
| `/distill` | Periodic — process 🗂️ event markers from current conversation into `resources/` notes |
| `/maintain` | Periodic vault operations — 6 options: generate artifacts, inbox processing, event processing, memory maintenance, resource note maintenance, reports |
| `/sync` | Git operations — commit staged work, check or pull framework updates |
| `/search` | Query vault by meaning (Tier 2/3 semantic via Qdrant) or keyword (Tier 1 ripgrep) |
| `/contribute` | Contribute framework improvements to upstream GitHub |

Adding a new command: create `.claude/commands/{name}.md`. No registration required. Avoid names that conflict with built-in Claude Code skills — built-ins take precedence on name collision.

---

### Automation reliability summary
*→ Distilled: [[personal/resources/ai-agent-hook-vs-instruction-reliability]]*

| Behavior | Mechanism | Reliability |
|---|---|---|
| Save conversation to `_conversations/` | Hook (`Stop` + `SessionEnd`) | Guaranteed |
| Load `_self/about.md` at session start | Hook (`inject-profile.py`) | Guaranteed — first turn only |
| Load `_self/rules.md` at session start | Hook (`inject-rules.py`) | Guaranteed — first turn only |
| Load project `CLAUDE.md` | Hook (`inject-context-claude.py`) | Guaranteed if project name in first message |
| Load project `_memory.md` | Hook (`inject-context-memory.py`) | Guaranteed if project name in first message |
| Emit event markers mid-conversation | CLAUDE.md instruction | Unreliable — mitigated by `/remember` judgment pass |
| Regenerate conversation + project indexes | Gitea Actions (`generate-artifacts.yml`) | Guaranteed on push to main |
| Generate `pending-events.md` | Gitea Actions (`generate-artifacts.yml`) | Guaranteed on push to main |
| Infer context and confirm with user | CLAUDE.md instruction | Unreliable |
| `/remember` trigger | User-invoked slash command | Reliable — user-triggered; session-scoped |
| `/distill` trigger | User-invoked slash command | Reliable — user-triggered; cross-session |
| `/maintain` trigger | User-invoked slash command | Reliable — user-triggered; periodic |

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

## Verification

Test scripts in `_tests/` verify requirements automatically. They run in Gitea Actions on every push to `main` (`.gitea/workflows/test.yml`). Each script is named after the requirement it covers.

| Test | Requirement | What it checks |
|---|---|---|
| `test_hook_budget.py` | R6 | Each hook-injected file: warn at 8,000 chars (80%), fail at 10,000 chars (100%) — checked independently per file |

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
| R6 — Hook budget | Four inject scripts, each with its own independent 10,000-char budget |
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

By convention: `origin` = your private git host (Gitea or GitHub fork); `upstream` = the public GitHub framework repo.

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
| Known limitations or roadmap | `docs/evolution.md` | — |
| Deployment tier detail | `docs/getting-started.md` | `docs/private-cloud-setup.md` or `docs/self-hosted-setup.md` |
| Repo layout or contribution workflow | `CONTRIBUTING.md` | — |
| System architecture or component interfaces | `architecture.md` (this file) | — |
| System requirements | `requirements.md` | — |
