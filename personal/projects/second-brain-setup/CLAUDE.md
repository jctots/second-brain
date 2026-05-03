# second-brain-setup — Project Instructions

[[second-brain-setup/index|⬅️ Project Index]]

## What this project is

The meta-project for designing and evolving this second brain. It captures the *why* behind how the system is structured — decisions, rationale, and design history that don't belong in operational CLAUDE.md files.

## Reference conventions

Use heading-anchor wikilinks for all cross-references within this project. Obsidian jumps to the heading; Foam degrades gracefully to file-level (no error).
- `R#` — `[[second-brain-setup/requirements#Rn — heading text|Rn]]` (e.g., `[[second-brain-setup/requirements#R2 — Platform portability|R2]]`)
- `A#` — `[[second-brain-setup/architecture#An — heading text|An]]` (e.g., `[[second-brain-setup/architecture#A2 — Gitea Actions workflows|A2]]`)
- `D#` — `[[second-brain-setup/decisions#Dn — YYYY-MM-DD — heading text|Dn]]` (e.g., `[[second-brain-setup/decisions#D83 — 2026-05-01 — Wikilinks use bare filenames within-project; Obsidian-primary with Foam two-step accepted|D83]]`)

## Key rules

The vault-wide system constraints live in root CLAUDE.md. The requirements and rationale behind each are documented here:
- Platform portability + reproducibility — [[second-brain-setup/requirements#R2 — Platform portability|R2]], [[second-brain-setup/requirements#R3 — Reproducibility|R3]]
- Gitea Actions for deterministic artifacts — [[second-brain-setup/architecture#A2 — Gitea Actions workflows|A2]], [[second-brain-setup/requirements#R5 — No always-on processes|R5]]
- Generated file sections are read-only — [[second-brain-setup/requirements#R7 — Generated artifacts are static|R7]]
- Public sync is judgment-driven; content paths never reach GitHub — [[second-brain-setup/requirements#R4 — Privacy / data sovereignty|R4]], [[second-brain-setup/requirements#R8 — Framework/content boundary|R8]]

## Root CLAUDE.md vs this file

Root CLAUDE.md holds vault-wide rules — anything that applies to every project and every conversation.
This file holds second-brain-setup-specific context: file roles, reference conventions.

When you discover a new vault-wide rule while working on this project (e.g., a wikilink convention, a privacy constraint), add it to root CLAUDE.md. Add the rationale as a decision in `decisions.md` and a cross-reference here if needed. Do not duplicate the rule in both files.

## Files

| File | Purpose | Use when |
|---|---|---|
| `index.md` | Project overview and entry point | — |
| `_memory.md` | Current state only — fixed sections updated in-place; bounded size for injection | Sync memory |
| `decisions.md` | Design history — decisions, reasoning, alternatives | *Why* was this built this way? Sync memory. |
| `roadmap.md` | Improvement backlog — items, skills inventory, starter prompts | *What* to build next? Sync memory for new items. |
| `requirements.md` | System requirements — tools, portability, privacy, format constraints | *What* must always be true? Manual updates only. |
| `architecture.md` | System structure, component interfaces, data flows, Claude Code interface spec | *What is it and how does it work?* Manual updates only. |