---
context: personal
para: projects
created: 2026-04-29
---

# Second Brain — Architecture

[[second-brain-setup/index|⬅️ Project Index]]

> System structure: components, responsibilities, interfaces, and data flows.
>
> Related: `requirements.md` (constraints this satisfies) · `decisions.md` (why it was built this way)

---

## Architecture principles

| # | Name | Summary | Location |
|---|---|---|---|
| A1 | Extended section pattern | Project `_memory.md` files use `<!-- extended -->` to split summary (injected) from lower-priority reference (file-only) | [§ A1](#a1--extended-section-pattern) |
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
  - [Continue.dev](#continuedev)
  - [Gitea Actions](#gitea-actions-ci)
  - [\_scripts/](#_scripts-shared-scripts)
- [Data flows](#data-flows)
- [Boundaries and ownership](#boundaries-and-ownership)
- [Claude Code interface](#claude-code-interface)
  - [Configuration surface](#configuration-surface)
  - [Hook events](#hook-events)
  - [Configured hooks](#configured-hooks)
  - [A1 — Extended section pattern](#a1--extended-section-pattern)
  - [A2 — Gitea Actions workflows](#a2--gitea-actions-workflows)
  - [CLAUDE.md](#claudemd)
  - [Auto-memory](#auto-memory)
  - [Slash commands](#slash-commands)
  - [Automation reliability summary](#automation-reliability-summary)
- [Continue.dev interface](#continuedev-interface)
  - [Configuration](#configuration)
  - [Context loading](#context-loading)
  - [Slash commands (Continue.dev)](#slash-commands-continuedev)
- [Verification](#verification)
- [Key constraints satisfied](#key-constraints-satisfied)
- [Artifact ecosystem](#artifact-ecosystem)
  - [The artifacts](#the-artifacts)
  - [Framework vs. content split](#framework-vs-content-split)
  - [Deployment tiers](#deployment-tiers)
  - [Contribution workflow](#contribution-workflow)

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
└──┬─────────────┬─────────────┬─────────────┬────────┘
   │             │             │             │
VSCode/Foam   Obsidian    Claude Code  Continue.dev
(editing/   (reading/    (SaaS AI)   (local-first AI)
 reading)    mobile)                       │
                                  ┌────────┴────────┐
                           Private Ollama/        Ollama
                           vLLM on VPS         (local LLM)
                           (private cloud)
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

### Continue.dev

Local-first AI reasoning layer. Uses Ollama to run LLMs locally — no data leaves the machine. Parallel path to Claude Code; both can be active simultaneously. The line between them is drawn by content sensitivity.

**Owns:** session reasoning on sensitive content, memory management, slash command execution
**Consumes:** vault via filesystem tools; context via `/load-context` slash command
**Does not own:** the vault (it assists, not governs); hook execution (Continue.dev has no hook system)

**Context loading at session start (user-triggered):**

```
User runs /load-context my-project
  → loads CLAUDE.md (root)
  → loads _self/about.md
  → loads _self/rules.md
  → loads project CLAUDE.md + _memory.md
```

Context is not injected automatically — the user runs `/load-context` at the start of each session. This is the key behavioral difference from Claude Code's hook-guaranteed injection.

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
| `save-conversation.py` | Hook (`Stop`, `SessionEnd`) | Save session transcript to `_conversations/` |
| `index-conversations.py` | CI | Regenerate `_conversations/index.md` |
| `update-project-indexes.py` | `/housekeeping`, `/sync-memory` | Update `## files` + `## relevant conversations` in project index.md |
| `commit.py` | `/commit` command | Stage → commit → pull rebase → push |

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
  → save-conversation.py → writes _conversations/YYYY/MM/YYYY-MM-DD-{title}.md
User pushes to Gitea
  → Gitea Actions triggers index-conversations.yml
      → index-conversations.py regenerates _conversations/index.md
      → CI commits result back to main
```

### Memory sync (user-triggered `/sync-memory`)

```
User runs /sync-memory
  → reads _inbox/memory-queue.md
      → groups entries by target file
      → for each target: reads file, consolidates candidates, drafts minimal update
      → writes each update using Edit (never Write)
      → removes processed entries from queue
  → if queue was empty: falls back to retrospective scan of current conversation
  → updates _self/about.md if new profile facts observed
  → updates _self/rules.md if behavioral correction warranted
  → prepends to decisions.md if an architectural decision was made
```

### Distill (user-triggered `/distill`)

```
User runs /distill
  → reads _inbox/distill-queue.md
  → for each pending entry:
      → reads source conversation file
      → drafts note content (structured, concise — areas/ or resources/)
      → presents: proposed path + draft content + placement reason
      → iterates with user until confirmed or skipped
      → on confirm: writes note (Edit if exists, Write if new); updates dashboard.md
      → on skip: leaves entry in queue unchanged
  → removes only confirmed entries from queue
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
**Budget:** Summary section ≤ 9,500 chars (warn at 7,600).

---

#### Project CLAUDE.md injection (`UserPromptSubmit`)

**File:** `_scripts/inject-context-claude.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Reads `hook_data["prompt"]` (falls back to first user message in transcript). Scans `personal/`, `professional/`, `public/` for any project whose name appears in the message. For each matched project, reads its `CLAUDE.md`, stripping at `<!-- extended -->`.
**Budget:** Summary section of `CLAUDE.md` ≤ 9,500 chars (warn at 7,600).

---

#### Project _memory.md injection (`UserPromptSubmit`)

**File:** `_scripts/inject-context-memory.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Same project-matching logic as above. Reads `_memory.md` for each matched project, stripping at `<!-- extended -->`.
**Budget:** Summary section of `_memory.md` ≤ 9,500 chars (warn at 7,600).

---

#### Feedback injection (`UserPromptSubmit`)

**File:** `_scripts/inject-rules.py`
**Fires on:** Every `UserPromptSubmit`, self-limits to first turn only
**What it does:** Reads `_self/rules.md`, strips everything at and below `<!-- extended -->`, outputs the summary section.
**Budget:** Summary section ≤ 9,500 chars (warn at 7,600).

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
6. Writes to `_conversations/YYYY/MM/YYYY-MM-DD-{ai-title-as-slug}.md`

**Known behavior:** Fires on every `Stop` — partial conversations are saved incrementally and overwritten with the same filename.

---

### A1 — Extended section pattern

Project `_memory.md` files may contain a `<!-- extended -->` marker. Inject scripts strip everything at and below the marker — only the summary section is injected. Content below holds lower-priority reference material: demoted decisions, superseded items.

**Edit rule:** always use the Edit tool (targeted replacement) on `_memory.md` files with this marker — Write (full overwrite) would erase the extended section.

---

### A2 — Gitea Actions workflows

**Design principle:** prefer CI for derived/generated artifacts; prefer local hooks only for things that must block a bad commit.

**Why two CI systems:** Gitea Actions runs on your private git host and has direct access to content paths (`_conversations/`, `_self/`, personal notes). GitHub Actions runs only on the public framework fork — it never has access to your content. This split is a privacy boundary, not just a technical preference. Content-aware workflows (indexing, budget tests on private files) must run on Gitea; framework tests run on either.

| Workflow | CI | Trigger | What it does |
|---|---|---|---|
| `index-conversations.yml` | Gitea Actions | Push to `main` when `_conversations/*.md` changes | Runs `index-conversations.py`, commits updated `_conversations/index.md` |
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

Workspace-scoped memory (`.claude/projects/.../memory/`) is **not used in this repo** (D94). All persistent memory lives in vault files:

| File | Content | Injected by |
|---|---|---|
| `_self/about.md` | Profile + behavioral patterns | `inject-profile.py` |
| `_self/rules.md` | Feedback rules and corrections | `inject-rules.py` |
| project `_memory.md` | Project state + open questions | `inject-context-memory.py` |

These files travel with the repo, are git-versioned, and are readable in Obsidian. Workspace-scoped memory is machine-local and not portable — it was retired for these reasons.

---

### Slash commands

Location: `.claude/commands/`

| Command | When to use |
|---|---|
| `/sync-memory` | Process `_inbox/memory-queue.md` — run when queue has items or at session end |
| `/distill` | Process `_inbox/distill-queue.md` — interactive, one entry at a time |
| `/housekeeping` | Periodic maintenance — classify conversations, check budgets, regenerate indexes |
| `/commit` | Stage and commit — Claude proposes commit message, user confirms |
| `/audit` | Scan all active projects for structural gaps — report only |
| `/review-memory` | Human audit of AI-maintained memory files — report only |

Adding a new command: create `.claude/commands/{name}.md`. No registration required.

---

### Automation reliability summary

| Behavior | Mechanism | Reliability |
|---|---|---|
| Save conversation to `_conversations/` | Hook (`Stop` + `SessionEnd`) | Guaranteed |
| Load `_self/about.md` at session start | Hook (`inject-profile.py`) | Guaranteed — first turn only |
| Load `_self/rules.md` at session start | Hook (`inject-rules.py`) | Guaranteed — first turn only |
| Load project `CLAUDE.md` | Hook (`inject-context-claude.py`) | Guaranteed if project name in first message |
| Load project `_memory.md` | Hook (`inject-context-memory.py`) | Guaranteed if project name in first message |
| Extended context footer signal | Inject scripts | Guaranteed when marker present |
| Regenerate conversation + project indexes | Gitea Actions | Guaranteed on push to main |
| Infer context and confirm with user | CLAUDE.md instruction | Unreliable |
| `/sync-memory` trigger | User-invoked slash command | Reliable — user-triggered |
| `/distill` trigger | User-invoked slash command | Reliable — user-triggered |

---

## Continue.dev interface

How Continue.dev integrates with this repo — configuration, context loading, and slash commands.

---

### Configuration

Continue.dev is configured via `~/.continue/config.json`. Add Ollama as a provider:

```json
{
  "models": [
    {
      "title": "Qwen 2.5 7B (local)",
      "provider": "ollama",
      "model": "qwen2.5:7b",
      "apiBase": "http://localhost:11434"
    }
  ]
}
```

For Tier 2 (private cloud), replace `localhost` with the VPS address and add HTTPS + API key auth. For Tier 3 (self-hosted), Ollama runs as a Docker container — use its container address instead of `localhost`. See `docs/self-hosted-setup.md`.

---

### Context loading

Continue.dev has no hook system. Context is loaded manually at session start via the `/load-context` slash command:

```
/load-context my-project
```

This loads root `CLAUDE.md`, `_self/about.md`, `_self/rules.md`, and the matched project's `CLAUDE.md` + `_memory.md` — the same files the four Claude Code hooks inject automatically.

**Reliability comparison:**

| Behavior | Claude Code | Continue.dev |
|---|---|---|
| Load `_self/about.md` | Hook — guaranteed first turn | `/load-context` — user-triggered |
| Load `_self/rules.md` | Hook — guaranteed first turn | `/load-context` — user-triggered |
| Load project `CLAUDE.md` | Hook — if project name in first message | `/load-context` — user-triggered |
| Load project `_memory.md` | Hook — if project name in first message | `/load-context` — user-triggered |

Individual files can also be loaded using Continue.dev's `@file` mentions.

**Context budget:** determined by the Ollama model in use — typically 32K–128K tokens. The `<!-- extended -->` marker in `_memory.md` still applies: keep summary sections above it to avoid loading unnecessary detail.

---

### Slash commands (Continue.dev)

Location: `.continue/prompts/`

Every Claude Code slash command has a Continue.dev equivalent. The invocation is the same in both tools — type `/command-name` in the chat panel.

| Command | Claude Code | Continue.dev |
|---|---|---|
| `/sync-memory` | `.claude/commands/sync-memory.md` | `.continue/prompts/sync-memory.md` |
| `/commit` | `.claude/commands/commit.md` | `.continue/prompts/commit.md` |
| `/housekeeping` | `.claude/commands/housekeeping.md` | `.continue/prompts/housekeeping.md` |
| `/audit` | `.claude/commands/audit.md` | `.continue/prompts/audit.md` |
| `/review-memory` | `.claude/commands/review-memory.md` | `.continue/prompts/review-memory.md` |

Adding a new command: create both `.claude/commands/{name}.md` and `.continue/prompts/{name}.md` to keep both paths in parity.

---

## Verification

Test scripts in `_tests/` verify requirements automatically. They run in Gitea Actions on every push to `main` (`.gitea/workflows/test.yml`). Each script is named after the requirement it covers.

| Test | Requirement | What it checks |
|---|---|---|
| `test_r6_hook_budget.py` | R6 | Each hook-injected file's summary section: warn at 7,600 chars (80%), fail at 9,500 chars (100%) — checked independently per file |

Tests are deterministic pass/fail scripts — stdlib Python only (R2), no Claude session required. When a test fails, CI blocks. Add a new test whenever a requirement becomes mechanically checkable.

---

## Key constraints satisfied

| Requirement | How |
|---|---|
| R1 — Obsidian + Foam | Static markdown, shortest-unique-path wikilinks, no plugin-dependent features |
| R2 — Platform portability | Python stdlib scripts, pathlib, no OS-specific calls |
| R3 — Reproducibility | `infra.yaml` + setup scripts; CI uses direct `run:` steps |
| R4 — Privacy | Three inference paths: cloud SaaS (conscious tradeoff), private cloud (Continue.dev + remote Ollama/vLLM on VPS), local (Continue.dev + local Ollama, air-gapped) |
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
`_scripts/` · `_templates/` · `.claude/` · `infra.yaml` · `_tests/` · root `CLAUDE.md`
Plus: second-brain-setup SE docs (`personal/projects/second-brain-setup/` excluding per-instance files)

**Content paths** (private, never leave your instance):
`personal/` · `professional/` · `_self/` · `_daily/` · `_conversations/` · `_inbox/`

### Deployment tiers

The system supports three deployment tiers, all built from the same upstream framework.

> GitHub (framework CI) and cloud SaaS AI remain available at all tiers — Tier 2 and Tier 3 add private paths, they don't remove the SaaS options.

| Tier | Name | Git hosting | AI inference | Hardware required |
|---|---|---|---|---|
| 1 | SaaS | GitHub | Cloud SaaS (e.g., Claude Code) | None |
| 2 | Private cloud | Gitea on VPS | Ollama/vLLM on VPS (HTTPS + API key) | None (VPS subscription) |
| 3 | Self-hosted | Gitea on homelab | Ollama on local machine | Homelab + GPU |

**Tier 1 — SaaS**

Framework: GitHub fork of the upstream. Content hosting: GitHub private fork. CI: GitHub Actions (framework tests only).

Privacy caveats: content is visible to cloud AI; content lives on GitHub. Not suitable for comprehensive capture of sensitive personal content. Use for: evaluating the framework, learning the design, contributing to the upstream.

**Tier 2 — Private cloud**

Framework: GitHub fork of the upstream (framework CI). Content hosting: Gitea on VPS. AI: Continue.dev configured with a remote Ollama or vLLM endpoint (HTTPS + API key) — no local GPU required. CI: Gitea Actions (content-aware: indexing, tests) + GitHub Actions (framework tests).

Privacy: content stays on user-controlled infrastructure; no local hardware beyond a laptop required.

**Tier 3 — Self-hosted**

Framework: GitHub fork of the upstream (framework CI). Content hosting: Gitea on homelab. AI: Continue.dev + local Ollama (no data leaves the machine). CI: Gitea Actions (content-aware: indexing, tests) + GitHub Actions (framework tests).

Privacy: content never leaves local infrastructure. Full feature set, maximum sovereignty. Use for: a real second brain with comprehensive capture of personal, professional, and sensitive content.

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
