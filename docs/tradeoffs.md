# ⚖️ Tradeoffs and Known Limitations

This setup involves real tradeoffs. The table below names them honestly — with impact and mitigation for each.

| Risk/Tradeoff | Impact | Mitigation |
|---|---|---|
| **📱 Mobile: no AI assistance** — Continue.dev + VS Code require a desktop | No AI-assisted editing from a phone | Install Obsidian mobile + the [obsidian-git plugin](https://github.com/Vinzent03/obsidian-git) — syncs your vault via git and gives full read access, navigation, and light capture from your phone. AI-assisted editing still requires VS Code. |
| **💻 Hardware requirement** — local LLM needs enough RAM/VRAM | Slow or unusable on low-spec machines; quality degrades with smaller models | Start with a 7B model (runs on most modern machines). Upgrade hardware or use the Claude Code path for heavier reasoning tasks. |
| **🤖 AI drift in memory files** — the agent writes `_memory.md` and your profile automatically | Stale or wrong content gets re-injected into future sessions, compounding errors | Run `/review-memory` regularly. Memory files are plain Markdown — read, correct, or delete any entry directly. Treat them as a draft, not ground truth. |
| **📈 Context budget creep** — instruction files grow silently | Context has a hard limit; truncation happens without warning, silently breaking injection | The `<!-- extended -->` delimiter caps what gets injected per file. `/housekeeping` flags files approaching the limit. |
| **🔗 AI tool dependency** — slash commands live in tool-specific folders (`.claude/commands/`, `.continue/prompts/`) | Adding a third AI tool requires a new set of prompt files | The instruction files (`CLAUDE.md`, `_memory.md`, `_self/`) are plain Markdown — they work with any tool that reads files. Only the invocation layer is tool-specific. |
| **🔍 Single-tool dependency for graph/search** — graph view and backlinks depend on Foam or Obsidian | Losing the tool removes those navigation features | Notes are plain Markdown with no proprietary syntax. Any compatible tool (Logseq, Notion import, etc.) works without data loss. |
| **☁️ Cloud path: data sent to Anthropic** — if using Claude Code, context is sent to the API | Project context (not the full vault) leaves your machine during sessions | Use Continue.dev + Ollama for sensitive content. Both paths can be active simultaneously — the line is yours to draw. See [PRIVACY.md](../PRIVACY.md). |
