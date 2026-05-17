# 🧬 Evolution

Current tradeoffs and planned improvements. Roadmap items that address a known tradeoff note it inline.

This is a personal project — there are no release dates or commitments. Items are grouped by rough horizon. Check the box when done.


## ⚖️ Known limitations

| Risk/Tradeoff | Impact | Mitigation |
|---|---|---|
| **📱 Mobile: no AI assistance** — Claude Code requires a desktop | No AI-assisted editing from a phone | Install Obsidian mobile + the [obsidian-git plugin](https://github.com/Vinzent03/obsidian-git) — syncs your vault via git and gives full read access, navigation, and light capture from your phone. AI-assisted editing still requires VS Code. |
| **💻 Hardware requirement** — local LLM needs enough RAM/VRAM | Slow or unusable on low-spec machines; quality degrades with smaller models | Start with a 7B model (runs on most modern machines). Upgrade hardware or use the Claude Code path for heavier reasoning tasks. |
| **🤖 AI drift in memory files** — the agent writes `_memory.md` and your profile automatically | Stale or wrong content gets re-injected into future sessions, compounding errors | Run `/maintain` regularly. Memory files are plain Markdown — read, correct, or delete any entry directly. Treat them as a draft, not ground truth. |
| **📈 Context budget creep** — instruction files grow silently | Context has a hard limit; truncation happens without warning, silently breaking injection | The `<!-- extended -->` delimiter caps what gets injected per file. `/maintain` flags files approaching the limit. |
| **🔗 AI tool dependency** — slash commands live in `.claude/commands/` | Switching AI tools requires rewriting prompt files | The instruction files (`CLAUDE.md`, `_memory.md`, `_self/`) are plain Markdown — they work with any tool that reads files. Only the invocation layer is tool-specific. |
| **🔍 Single-tool dependency for graph/search** — graph view and backlinks depend on Foam or Obsidian | Losing the tool removes those navigation features | Notes are plain Markdown with no proprietary syntax. Any compatible tool (Logseq, Notion import, etc.) works without data loss. |
| **☁️ Tier 1: data sent to Anthropic** — at Tier 1, context is sent to Anthropic's API | Project context leaves your machine during sessions | Use Tier 2 or Tier 3 for sensitive content — set `ANTHROPIC_BASE_URL` to route inference through LiteLLM + Ollama instead. The line is yours to draw per session. See [PRIVACY.md](../PRIVACY.md). |
| **🔍 Tier 1: keyword search only** — semantic search (RAG) requires Qdrant, which is only available at Tier 2/3 | Notes are retrieved by keyword match, not meaning — connections between notes are invisible unless you already know they exist | Tier 2/3: Qdrant + `embeddinggemma:latest` via Ollama; active search via `/search`, passive surfacing via `inject-context-rag.py` hook each turn. |


## 🎯 Near-term

- [x] **Gitea Actions workflow** — CI pipeline: auto-generates `_conversations/index.md`, project indexes, dashboard, and PDF sidecars on push
- [ ] **Automated sanitization** — replace manual flag-and-review with a regex pass that substitutes known patterns automatically, reducing friction on each sync to upstream
- [ ] **Weekly review command** — a `/review` command that runs a structured weekly reflection: inbox status, project health check, open action items. Produces a dated review note.


## 🔭 Medium-term

- [x] **Semantic search across vault** — query notes by meaning, not just keyword. Implemented via Qdrant + Ollama (`embeddinggemma:latest`) at Tier 2/3. Active search via `/search`; passive surfacing via `inject-context-rag.py` hook.
- [x] **Mobile capture workflow** — a lightweight path for quick inbox drops from mobile without VS Code. Implemented via Obsidian mobile + obsidian-git on a dedicated `mobile` branch; `/sync` merges back to `main`.
- [x] **Maps of Content (MOC) generation** — covered by the generated dashboard (CI-built hub note with tag-grouped resource links) and `/distill` for manual extraction.


## 💭 Ideas (not committed)

- [ ] **Multi-agent pattern for long tasks** — spawn parallel subagents for research + draft + review on complex notes.
- [x] **Cross-vault search command** — searches across personal/, professional/, and public/ simultaneously, returning ranked results with PARA category and project context. Implemented via `/search` + Qdrant (Tier 2/3).
- [ ] **Obsidian plugin integration** — context loading from within Obsidian, without needing VS Code open.
- [ ] **Proactive/heartbeat agent** — a scheduled process that reviews recent `_inbox/` and `_daily/` entries and surfaces patterns or action items without being explicitly asked.
- [ ] **Cross-CLI harness compatibility** — evaluate whether the harness (hooks, slash commands, context injection) transfers to other AI CLIs. The vault files and scripts are tool-agnostic; document what is Claude Code–specific and what a porting guide would need to cover.


## 💬 Contributing ideas

Have a feature idea or found a gap? Open a [feature request](https://github.com/jctots/second-brain/issues/new?template=feature_request.md). See [CONTRIBUTING.md](../CONTRIBUTING.md) for how this project handles contributions.
