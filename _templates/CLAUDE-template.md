<!--
Template: CLAUDE.md
Use: Place one CLAUDE.md in each active project folder.
Injected by hook at session start when the project name appears in the first message.
Budget: combined CLAUDE.md + _memory.md summary sections must stay ≤ 6,666 chars.
See personal/projects/second-brain-setup/reference.md for hook injection details.
-->

# {project-name} — Project Instructions

[[{project-name}/index|⬅️ Project Index]]

## What this project is

One or two sentences on the project goal and scope.

## Design constraints

Any hard constraints Claude must check before proposing changes. Remove this section if there are none.

## Files

| File | Purpose | Use when |
|---|---|---|
| `index.md` | Project overview and entry point | — |
| `_memory.md` | Current state — fixed sections updated in-place | — |
| `reference.md` | Inputs, stable facts, lookup material — starts as a brief, grows over time | *What is this / how does it work?* |

Optional files — create when the signal appears, not before:
- `decisions/` — when `_memory.md` Key decisions gets long. Create a `decisions/` folder with `index.md` (newest-first table) and one file per decision (`D{n}-{slug}.md`, using `_templates/decision-template.md`). To add a new decision: create the file, increment D# from the index, add a row to `index.md`.
- `roadmap.md` — when next-actions or a backlog outgrows `index.md` or `_memory.md`. Good candidate for a scheduled agent.
- `requirements.md` + `architecture.md` — only if `reference.md` grows distinct "constraints" and "structure" sections consulted separately. Most projects never reach this.

## On sync memory

When sync memory runs and this project is involved:

1. Update `_memory.md` — update existing sections in-place. Do not append new blocks.
2. If a significant decision was made: create `decisions/D{n}-{slug}.md` if `decisions/` exists, otherwise record it in `_memory.md` under Key decisions.

**What qualifies as a decision:** {project-specific guidance — strategy changes, tool choices, design tradeoffs; not routine implementation details}
