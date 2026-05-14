# Second Brain — Claude Instructions

[[dashboard|⬅️ Dashboard]]

## System Overview

This second brain uses the **PARA method** across **three contexts**:

| Context         | Audience        | Nature                                      | Rules                                                                                                                                   |
| --------------- | --------------- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `personal/`     | Self and family | Private — life, health, finances, family    | Treat all content as private. **Default context** — use unless there is a reason to choose otherwise.                                   |
| `professional/` | Professional    | Private — career, current job, clients      | Treat all content as private. For current employer / company work only — not job search or CV (those live in `personal/`).              |
| `public/`       | Anyone          | Shareable — open source, writing, learning  | Content may eventually be published — write with a reader in mind. Do not embed personal details, employer names, or private decisions. Use only when content is intended for sharing or publishing — not merely because it isn't sensitive. |

Each context has the same PARA structure:

```
{context}/
├── projects/   ← active work with a defined outcome and deadline
├── areas/      ← ongoing responsibilities with no end date
├── resources/  ← reference material, topics of interest
└── archive/    ← completed or inactive items from above
```

### Special root folders

| Folder            | Purpose                                                                |
| ----------------- | ---------------------------------------------------------------------- |
| `_conversations/`   | Saved Claude Code session transcripts                                  |
| `_daily/`           | Mixed daily notes — time-indexed, spans all contexts                   |
| `_inbox/`           | Capture zone — no context yet, process and move out                    |
| `_infrastructure/`  | Infrastructure stack — `stack.yaml` (tooling manifest) + Docker Compose for Tier 2/3 |
| `_scripts/`         | Automation scripts (indexing, hook injection, conversation saving)     |
| `_self/`            | AI-maintained profile and behavioral reflection about the user         |
| `_templates/`       | Note templates — each file is self-documenting with usage instructions |
| `_tests/`           | Tests for scripts and hook budget enforcement                          |

## PARA lifecycle

### Transitions

| From | To | Trigger |
|---|---|---|
| `projects/` | `areas/` | Defining goal met; ongoing responsibility remains |
| `projects/` | `archive/` | Defining goal met; no ongoing responsibility |
| `areas/` | `archive/` | Responsibility ends entirely |
| `projects/` or `areas/` | `resources/` | Never directly — extract stable knowledge via `/distill` instead |

**What creates each category:**
- `projects/` — user intent: an active goal with a horizon
- `areas/` — a completed project whose responsibility continues, or an explicitly recognized ongoing responsibility with no current goal
- `resources/` — extracted from conversations or mature project/area docs via `/distill`
- `archive/` — completed or abandoned items from any category

**projects/ vs. areas/ test:** Ask *"Is there a defining goal I'm still working toward?"* If yes → `projects/`. Long-running systems (home lab, second brain) stay in `projects/` as long as there are open goals and active structured work.

### Enforcement

When creating or placing a note, verify the category fits. Flag before writing if it doesn't:

- `projects/` with no defined goal or open question → suggest `areas/`
- `areas/` with an active bounded goal → suggest `projects/`
- `projects/` or `areas/` that is pure stable reference → suggest extracting to `resources/` via `/distill`

Flag as: _"This looks like [category] rather than [proposed]. Want me to adjust the path?"_

## Conventions

### Naming

- Files: `kebab-case.md`
- Daily notes: `YYYY-MM-DD.md`
- Claude conversations: `_conversations/YYYY/MM/YYYY-MM-DD-{title-in-claude-code-ui}.md`

### Frontmatter fields

```yaml
---
context: personal | professional | public
para: projects | areas | resources | archive
tags: []
created: YYYY-MM-DD
---
```

### Wikilinks

| Case                                 | Format                                 | Notes                                                                   |
| ------------------------------------ | -------------------------------------- | ----------------------------------------------------------------------- |
| Unique filename (daily, inbox, self) | `[[filename]]`                         | Filename is already the display text                                    |
| Project index                        | `[[project_name/index\|project_name]]` | Alias = project name (same as folder); prevents "index" as display text |
| Other project file                   | `[[project_name/filename]]`            | Prefix for safe resolution; filename stem is already the display text   |

**`|` vs `\|`:** Use `\|` as the alias separator only inside table cells — the backslash prevents the pipe from breaking the table. In standalone lines, use plain `|`.

### Note maturity

- `_inbox/` → raw capture, no formatting required
- `areas/` and `resources/` → structured, kept up to date
- `projects/` → has a clear goal and `_memory.md`

## System constraints

- All scripts and hooks must work on Windows and Linux/macOS; a fresh clone must reach the same state via setup scripts
- Prefer Gitea Actions for deterministic artifacts (indexes, summaries); local hooks only for commit-blocking validation
- No always-on processes — Gitea Actions for scheduled work, not daemons or persistent MCP servers as hard dependencies
- Never edit generated file sections (`_conversations/index.md`, `## files` and `## relevant conversations` in project `index.md` files)
- Public sync is judgment-driven (`/publish`), never automated; content paths never reach GitHub

## Project files

Default set for any active project: `index.md`, `CLAUDE.md`, `_memory.md`, `reference.md`.

`reference.md` is always present — start it with inputs (brief, base repo, concept note) and let it grow into stable lookup material. Create optional files only when the signal appears:

- `decisions/` — when `_memory.md` "Key decisions" gets long. Create a `decisions/` folder with `index.md` (newest-first table of all decisions) and one file per decision (`D{n}-{slug}.md`, using `_templates/decision-template.md`). To add a new decision: create the file, increment D# from the index, add a row to `index.md`.
- `roadmap.md` — when next-actions or a skills/research backlog outgrows `index.md` or `_memory.md`. Good candidate for a scheduled agent.
- `requirements.md` + `architecture.md` — only if `reference.md` grows distinct "constraints" and "structure" sections that are frequently consulted separately. Most projects never need this.

## Project memory

Each active project folder may contain a `_memory.md` file — a running log of what Claude has learned about this project: decisions made, open questions, current status, and relevant context.

**Trigger:** Run `/remember` at the end of any conversation. Steps are defined in `.claude/commands/remember.md`.

**Quick status rules:** `status:` describes project state at milestone level — accurate for days or weeks, not tied to a specific pending action. `next:` lists meaningful project actions only — no git ops, no `/remember`, no housekeeping.

**Reminder:** At the end of each working session, if 🧠, 🗂️, or ✅ event markers were emitted during the conversation and `/remember` or `/distill` has not been run, remind the user: _"Events were captured this session — run `/remember` and/or `/distill` to process them."_

## Context at conversation start

At the start of each conversation, infer which context (personal/professional/public), PARA category, and project is most relevant based on the first message. State your guess and ask for confirmation before proceeding.

Example: _"This looks like `personal/projects/health-tracking`. Should I load that context?"_

When project names are mentioned in the first message, `_scripts/inject-context.py` automatically injects their `CLAUDE.md` and `_memory.md` into the context window. If a project was mentioned but its context was not injected (hook miss or later message), search for it at `{personal,professional,public}/projects/{name}/` — not with a filename glob.

**Hook verification:** At the start of every conversation, state in one line which project context files were loaded, e.g.: _"Loaded: `personal/projects/second-brain-setup/CLAUDE.md` + `_memory.md`"_. If no project context was injected, say so. This lets you verify hook status without asking.

## How to help me

- When I share a note, help me place it in the right context and PARA category
- `_self/about.md`, `_self/corrections.md`, and project context files are auto-injected by hook on the first turn — no need to re-read them unless the hook missed something
- **Do not write to workspace-scoped memory** (`~/.claude/projects/.../memory/`). All persistent memory for this vault lives in vault files: `_self/about.md` (profile + behavior), `_self/corrections.md` (corrections and known failure modes), and project `_memory.md` files. Use `/remember` to persist anything worth keeping.
- If a project was mentioned but context files are missing, search `{personal,professional,public}/projects/{name}/` and read `CLAUDE.md` and `_memory.md` manually
- When creating a new note or project file, check `_templates/` first for a relevant template
- Prefer editing existing notes over creating new ones
- Flag if a note in `_inbox/` has been sitting there too long without processing


## During-conversation captures

Evaluate independently throughout the conversation. A single exchange may trigger multiple events.

Emit each marker on its own line immediately after the relevant response. Include a one-line description. Do not elaborate or branch the conversation.

**🧠 `[memory event]`** — project state change, key decision, or anything worth persisting to project `_memory.md`. A key decision is any non-obvious choice where the why matters: rationale isn't self-evident, alternatives were weighed, or the trade-off has lasting consequences.
Format: `🧠 [memory event]: one-line description`

**👤 `[profile event]`** — profile fact or behavioral observation about the user. Profile facts → `_self/about.md`; behavioral corrections or feedback rules → `_self/corrections.md`; pure self-awareness observations (no Claude action) → `_self/reflection.md`. Handled by `/remember` inline and `/maintain` option 2 backstop.
Format: `👤 [profile event]: one-line description`

**🗂️ `[distill event]`** — lasting reference value beyond this project: technology analysis, tool comparisons, design patterns, architectural concepts, mental models. Does not trigger for project-specific decisions or ephemeral details.
Format: `🗂️ [distill event]: one-line description`

**✅ `[task event]`** — concrete next action identified for the user. Visual signal only — not routed by `/remember`; use judgment to include task-relevant content in the `_memory.md` block.
Format: `✅ [task event]: one-line description`

**📖 `[retrieve: path]`** — vault note flagged as relevant and worth reading in full. Emit when a title surfaced by the RAG hook seems directly useful to the current task. If the user confirms, read the file directly using your tools. Visual signal only — not routed by `/remember`.
Format: `📖 [retrieve: path/to/note.md]`

These markers are scanned by `save-conversation.py` and written to the conversation frontmatter as `events: [memory, profile, distill, task]`. `/remember` makes a judgment pass over the current conversation — markers are signals, not the authoritative source. Missed conversations are caught by `/maintain` via `_conversations/pending-events.md` (CI-generated).

**Processed markers** — emit immediately after actioning an event. Scanned by `save-conversation.py` into the `processed` frontmatter field.

- `🔁 [remember processed]` — emit via `/remember` only if `_memory.md` was written
- `🪪 [profile processed]` — emit via `/remember` only if a `_self/` file was written
- `📋 [task processed]` — emit via `/remember`, **or emit inline immediately after completing a `✅` task directly in this conversation**
- `📦 [distill processed]` — emit via `/distill` after writing to `resources/`

## Token and cost awareness

- If a task is open-ended or scope is unclear, ask one clarifying question before starting — this is cheaper than doing too much and redoing it.
- For simple, single-location edits: describe exactly what to type and where so the user can do it themselves.
- For complex edits (multiple files, generated content, structural changes): offer to do it, but note it will consume tokens.
- Default to "tell the user what to do" unless the change is too involved to describe concisely.

## Hook injection budget

Each injected file (`_self/about.md`, `_self/corrections.md`, project `CLAUDE.md`, project `_memory.md`) has a 10,000-char hard limit; warn at 8,000 (80%); consolidation target is 5,000 chars. `/remember` appends — never edits sections in-place. `/maintain` option 4 absorbs appended blocks into proper sections and consolidates to within budget.
