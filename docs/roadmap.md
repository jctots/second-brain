# 🗺️ Roadmap

This is a personal project — there are no release dates or commitments. Items are grouped by rough horizon. Check the box when done.


## 🎯 Near-term

- [ ] **GitHub Actions workflow** — equivalent of a CI pipeline: auto-generates `_conversations/index.md` and project indexes on push
- [ ] **Automated sanitization** — replace manual flag-and-review with a regex pass that substitutes known patterns automatically, reducing friction on each sync to the upstream


## 🔭 Medium-term

- [ ] **Semantic search across vault** — query notes by meaning, not just keyword. Likely via an MCP server for Continue.dev or an Obsidian plugin (Dataview + embeddings). Goal: surface connections you didn't know existed.
- [ ] **Mobile capture workflow** — a lightweight path for quick inbox drops from mobile without VS Code. Likely Obsidian mobile + obsidian-git, or a minimal web form writing to the vault via the git API.
- [ ] **Maps of Content (MOC) generation** — a command that generates or updates a hub note for a topic, linking all related notes grouped semantically. Obsidian Dataview may cover this natively.


## 💭 Ideas (not committed)

- [ ] **Multi-agent pattern for long tasks** — spawn parallel subagents for research + draft + review on complex notes.
- [ ] **Cross-vault search command** — searches across personal/, professional/, and public/ simultaneously, returning ranked results with PARA category and project context.
- [ ] **Obsidian plugin integration** — context loading from within Obsidian, without needing VS Code open.
- [ ] **Proactive/heartbeat agent** — a scheduled process that reviews recent `_inbox/` and `_daily/` entries and surfaces patterns or action items without being explicitly asked.


## 💬 Contributing ideas

Have a feature idea or found a gap? Open a [feature request](https://github.com/jctots/second-brain/issues/new?template=feature_request.md). See [CONTRIBUTING.md](../CONTRIBUTING.md) for how this project handles contributions.
