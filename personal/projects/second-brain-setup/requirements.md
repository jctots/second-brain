---
context: personal
para: projects
created: 2026-04-29
---

# Second Brain — Requirements

[[second-brain-setup/index|⬅️ Project Index]]

> **What belongs here:** Standing constraints — things that must always be true, independent of implementation. Stated as "the system SHALL..." and testable at any point in time. Doesn't change unless user needs change.
>
> **What belongs in `decisions.md`:** Past choices between alternatives, with rationale — "we chose X over Y because Z." Decisions point back to the requirement that motivated them. They may be superseded; requirements don't get superseded, they get revised.
>
> Related: `decisions.md` (how requirements were met) · `CLAUDE.md` (operational instructions)

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
- A local LLM tool (e.g. Ollama) is the preferred path for sensitive or routine tasks — see roadmap
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

| Hook | File | Warn | Hard limit |
|---|---|---|---|
| `inject-profile.py` | `_self/about.md` | 7,600 chars (80%) | 9,500 chars |
| `inject-rules.py` | `_self/rules.md` | 7,600 chars (80%) | 9,500 chars |
| `inject-context-claude.py` | project `CLAUDE.md` | 7,600 chars (80%) | 9,500 chars |
| `inject-context-memory.py` | project `_memory.md` | 7,600 chars (80%) | 9,500 chars |

**Implications:**
- Use `<!-- extended -->` marker to preserve detail without inflating the injected payload
- Summary section of each file is what counts — only content above `<!-- extended -->` is injected
- Growing content belongs here (`requirements.md`) or in extended sections, not in hook-injected files

**Verified by:** `_tests/test_r6_hook_budget.py` — warns at 80%, fails CI at 100%; runs on every push via `.gitea/workflows/test.yml`

---

## R7 — Generated artifacts are static

Index files and project file lists are generated artifacts, never edited manually.

**Implications:**
- `_conversations/index.md` is owned by `index-conversations.py`
- `## files` and `## relevant conversations` sections in project `index.md` files are owned by `update-project-indexes.py`
- Tool-agnostic constraint: generated files must render correctly in Obsidian and Foam without plugins

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

The system must support capture without requiring immediate processing. During a session, items of interest are silently queued to `_inbox/memory-queue.md` (memory candidates) and `_inbox/distill-queue.md` (note candidates) and processed on demand via `/sync-memory` and `/distill`. The queue entry format defined in root `CLAUDE.md` is a standing constraint — entries that deviate from it are not processable.

**Implications:**
- `_inbox/memory-queue.md` and `_inbox/distill-queue.md` are append-only capture zones during a session
- Format conformance is required for machine-processability; freeform entries are not valid
- Queued capture keeps sessions focused — items are logged without branching the current task
