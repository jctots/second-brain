<!--
Template: index.md
Use: Entry point for each active project folder.
Keep ## files and ## relevant conversations current as the project evolves.
Wikilinks: [[filename|Display title]] in lists; [[filename]] bare in tables (| conflicts with column separator); [[folder/index\|name]] in tables only when path-prefix required for unambiguous cross-project resolution

Default file set: index.md, CLAUDE.md, _memory.md, reference.md
  reference.md — always present; start with inputs (brief, base repo, concept note) and
    let it grow into stable lookup material over time.

Optional files — create when the signal appears, not before:
  decisions/ — when _memory.md "Key decisions" gets long. Create a decisions/ folder with
    index.md (newest-first table) and one file per decision (D{n}-{slug}.md).
  roadmap.md — when next-actions or a skills/research backlog outgrows index.md or _memory.md.
    Good candidate for a scheduled agent (research, progress tracking).
  requirements.md + architecture.md — only if reference.md grows distinct "constraints" and
    "structure" sections that are frequently consulted separately. Most projects never reach this.
-->

---
context: personal | professional | public
para: projects | areas | resources | archive
tags: [project]
created: YYYY-MM-DD
---

# {project-name}

[[dashboard|⬅️ Dashboard]]

One-line description of this project.

## files

- [[CLAUDE|{project-name} — Project Instructions]]
- [[_memory|{project-name} — Project Memory]]
- [[reference|{project-name} — Reference]]

## relevant conversations

- [[YYYY-MM-DD-conversation-slug|Conversation title]]
