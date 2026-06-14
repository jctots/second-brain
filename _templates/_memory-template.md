<!--
Template: _memory.md
Use: Place one _memory.md in each active project folder (e.g. personal/projects/my-project/_memory.md).
Claude reads this at the start of every session in that project and updates it on "/remember".

Required sections (all projects): Current status, Key decisions, Open questions.
Optional sections: add project-specific sections between Key decisions and Open questions
  (e.g. "Infrastructure inventory", "Design constraints", "People and roles").
On /remember, Claude updates each section in-place — never appends new blocks.
-->

# Project Memory — {project-name}

[[{project-name}/index|⬅️ Project Index]]

> Maintained by Claude. Updated on "/remember" trigger.
> Last updated: YYYY-MM-DD

## Snapshot

<!-- One line. Read by inject-context-projects.py for the Active Projects registry.
     Accurate for days or weeks. Format: {milestone/version} — {one-phrase state}. -->
One-line summary of where this project stands right now

## Next Actions

<!-- Meaningful project actions only — no git ops, no /remember, no housekeeping. -->
- First next action
- Second next action

## Working Context

<!-- One paragraph. Read at session start as working context for Claude. Replace (not accumulate) on each /remember.
     Covers: active state, repo/version, what changed this session.
     Stable reference (config, URLs, inventories) → reference.md. Prior-session detail → git history. -->
Brief description of where this project stands right now.

## Key decisions

<!-- Holding area for decisions until decisions/ is warranted.
     Create decisions/ folder when this section gets long or reasoning needs more space. -->
- Decision made and why

<!-- Add project-specific sections here if useful -->

## Open questions

- Things still unresolved
