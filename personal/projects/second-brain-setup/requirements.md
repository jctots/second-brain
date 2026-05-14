---
context: personal
para: projects
created: 2026-04-29
---

# Second Brain — Requirements

[[second-brain-setup/index|⬅️ Project Index]]

> **What belongs here:** Standing constraints — things that must always be true, independent of implementation. Stated as "the system SHALL..." and testable at any point in time. Doesn't change unless user needs change.
>
> **What belongs in `decisions/`:** Past choices between alternatives, with rationale — "we chose X over Y because Z." Decisions point back to the requirement that motivated them. They may be superseded; requirements don't get superseded, they get revised.
>
> Related: `decisions/` (how requirements were met) · `CLAUDE.md` (operational instructions)

## Traceability

| Req | Name | Architecture | Tests |
|---|---|---|---|
| R1 | Supported tools | — | — |
| R2 | Platform portability | — | — |
| R3 | Reproducibility | — | — |
| R4 | Privacy / data sovereignty | — | — |
| R5 | No always-on processes | A2 | — |
| R6 | Hook injection budget | — | T1.1–T1.8; T2.7–T2.8 |
| R7 | Generated artifacts are static | A2 | T4.3,T4.13–T4.17; T5.1–T5.22 |
| R8 | Framework/content boundary | — | — |
| R9 | Contributor workflow parity | — | — |
| R10 | Deferred capture | A1 | T3.1–T3.32; T4.1–T4.2,T4.9–T4.12 |
| R11 | Script and hook resilience | A3 | T1.3–T1.4,T1.8; T2.1,T2.4–T2.6,T2.9–T2.14,T2.17–T2.19,T2.21–T2.22,T2.24–T2.28,T2.32–T2.33,T2.38–T2.39; T3.7,T3.20,T3.25,T3.29–T3.30,T3.33–T3.39; T4.4–T4.8,T4.15; T5.10–T5.11,T5.16–T5.17,T5.21 |

---

## R1 — Supported tools

The vault must work correctly with all of the following:

| Tool | Role |
|---|---|
| Obsidian desktop | Primary reading, navigation, writing |
| Obsidian mobile + obsidian-git plugin | Mobile reading and capture |
| Foam (VSCode extension) | Editing, wikilink resolution in VSCode |

**Implications:**
- Wikilinks use shortest unique path with alias: `[[folder/filename|display]]`
- Folder entry points use explicit `/index`: `[[project-name/index|project-name]]` — Foam resolves `[[folder-name]]` → `index.md` natively, Obsidian does not; Obsidian aliases do not work for wikilink resolution
- Generated files must be static markdown — no Obsidian-only features (Dataview queries, plugin-dependent callouts)
- Frontmatter must be valid YAML parseable by all three tools

---

## R2 — Platform portability

All scripts, hooks, and setup steps must work on Windows (primary) and Linux/macOS (CI runner, secondary dev).

**Implications:**
- Scripts in Python, stdlib only, no OS-specific calls
- No PowerShell-only or bash-only scripts in `_scripts/` — platform-specific setup helpers (`.ps1`, `.sh`) are allowed for setup only
- Use `pathlib` for all path handling; never hardcode separators
- Scripts in `_scripts/` that require external packages must be CI-only and isolated in a CI venv; they must not be called by hooks or invoked without that venv. Hook scripts must remain stdlib-only.

---

## R3 — Reproducibility

A fresh clone on a new machine must reach the exact same state by running `_scripts/setup.sh` or `_scripts/setup.ps1`.

**Implications:**
- All tooling declared in `infra.yaml` — single source of truth for infrastructure
- No dependency on machine-local config not tracked in the repo
- No devcontainer — hooks run on the host, not in a container

---

## R4 — Privacy / data sovereignty

The vault is comprehensive by design — personal, professional, health, financial content will be present. Content discipline (filtering what you capture) is not a valid mitigation.

**Implications:**
- Cloud AI (e.g. Claude Code) is accepted for complex reasoning tasks where exposure is a conscious tradeoff
- Local LLM inference (Ollama) is the preferred path for sensitive or routine tasks. Claude Code connects to Ollama via a LiteLLM gateway (`ANTHROPIC_BASE_URL`) — the harness (hooks, slash commands, conversation saving) remains identical; only the inference backend changes. See `architecture.md` for tier configurations.
- A private cloud path (open-weights model on user-controlled infrastructure, encrypted API transport) bridges cloud SaaS and local — no client-side hardware required, inference stays within user-controlled infrastructure. Trust model: the user controls where inference happens, not whether inference is encrypted (the model sees plaintext during processing).
- The upstream repository must never contain private content; this is enforced structurally by `.gitignore` (see R8), not by manual curation

---

## R5 — No always-on processes

The system must not require background services to function.

**Implications:**
- No MCP servers with a persistent process as a hard dependency for core functionality
- Scheduled automation via Gitea Actions (CI), not local daemons
- Hook scripts must be fast and self-contained

---

## R6 — Hook injection budget

Claude Code caps each hook command's output independently at ~10,000 characters; output beyond that is redirected to a file reference instead of being injected into context. Each inject script has its own independent budget.

| Hook | File | Warn | Hard limit | Consolidation target |
|---|---|---|---|---|
| `inject-profile.py` | `_self/about.md` | 8,000 chars (80%) | 10,000 chars | 5,000 chars |
| `inject-rules.py` | `_self/rules.md` | 8,000 chars (80%) | 10,000 chars | 5,000 chars |
| `inject-context-claude.py` | project `CLAUDE.md` | 8,000 chars (80%) | 10,000 chars | 5,000 chars |
| `inject-context-memory.py` | project `_memory.md` | 8,000 chars (80%) | 10,000 chars | 5,000 chars |

**Implications:**
- `/remember` appends timestamped blocks — no in-place editing of sections
- `/maintain` option 4 consolidates files at the warning threshold, targeting 5,000 chars
- Aging content routes to `decisions/`, `resources/`, or is dropped — not preserved in an extended section

**Verified by:** T1.1–T1.8; T2.7–T2.8

---

## R7 — Generated artifacts are static

Index files and project file lists are generated artifacts, never edited manually.

**Implications:**
- `_conversations/index.md` is owned by `index-conversations.py`
- `_conversations/pending-events.md` is owned by `generate-pending-events.py`
- `## files` and `## relevant conversations` sections in project `index.md` files are owned by `update-project-indexes.py`
- Tool-agnostic constraint: generated files must render correctly in Obsidian and Foam without plugins

**Verified by:** T4.3,T4.13–T4.17; T5.1–T5.22

---

## R8 — Framework/content boundary

The framework and content layers must be structurally separated and enforced at the git level — not by convention alone.

**Implications:**
- The upstream repository's `.gitignore` must exclude all content paths: `personal/`, `professional/`, `public/`, `_self/`, `_daily/`, `_conversations/`, `_inbox/`
- Downstream instances (your instance, a community fork) inherit this boundary by default — a new forker cannot accidentally push content to their public GitHub fork
- Framework improvements flow via branch → PR to the upstream; content paths are never candidates for sync

---

## R9 — Contributor workflow parity

No contributor has a privileged path to the public repository. The repository owner contributes via the same branch → PR workflow as any community member.

**Implications:**
- Direct pushes to `main` are not used for framework improvements — branch → PR is the only path for all contributors including the owner
- The owner's instance is a downstream fork, structurally identical to any community member's instance
- The owner validates the contribution workflow by using it themselves — any friction they encounter is assumed to affect all contributors

---

## R10 — Deferred capture

The system must support capture without requiring immediate processing. During a session, the AI emits inline event markers (`🧠 [memory event]`, `🗂️ [distill event]`, `✅ [task event]`) with a one-line description. These are scanned by `save-conversation.py` and written to conversation frontmatter (`events`, `processed`). Processing happens on demand via `/remember` and `/distill`. Missed sessions are surfaced by `_conversations/pending-events.md` (CI-generated).

**Implications:**
- The conversation file is the source of truth — no separate queue files
- Marker format defined in root `CLAUDE.md` is a standing constraint — markers without the correct prefix are not detected
- Deferred capture keeps sessions focused — markers are emitted without branching the current task
- `/maintain` option 2 serves as the backstop for sessions where `/remember` or `/distill` was not run

**Verified by:** T3.1–T3.32; T4.1–T4.2,T4.9–T4.12

---

## R11 — Script and hook resilience

Every script and hook in `_scripts/` must exit 0 and not raise an unhandled exception when given:
- Empty or missing stdin input
- Malformed JSON input
- Missing files referenced by the hook (e.g. `_self/about.md`, project `CLAUDE.md`)
- Invocation outside expected turn order (e.g. a hook called on a second turn)
- Partial or empty vault state (e.g. no projects directory, empty `_conversations/`)

**Implications:**
- A crashing hook blocks all Claude Code operation for the session — silent failure (empty output, exit 0) is always preferable to an exception
- Generator scripts called by CI must handle empty or partial vault state without exiting non-zero
- Missing input files must produce empty output, not a stack trace

**Verified by:** T1.3–T1.4,T1.8; T2.1,T2.4–T2.6,T2.9–T2.14,T2.17–T2.19,T2.21–T2.22,T2.24–T2.28,T2.32–T2.33,T2.38–T2.39; T3.7,T3.20,T3.25,T3.29–T3.30,T3.33–T3.39; T4.4–T4.8,T4.15; T5.10–T5.11,T5.16–T5.17,T5.21
