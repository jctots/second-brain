# 🧠 second-brain

> "You do not rise to the level of your goals. You fall to the level of your systems."
> — James Clear

A workspace where an AI carries context across your projects — remembering decisions, surfacing knowledge that survives across models and sessions, and retrieving past reasoning when you need it. Use frontier models for the best reasoning, or run a local model to keep your data private.

## 🔍 The problem

Working on a project with an AI assistant is powerful — until you close the tab. The next session starts from zero: no memory of what you decided, why you rejected an approach, or where you left off.

Claude.ai Projects and ChatGPT solve this with built-in memory, but you don't own the output — no versioning, no offline copy, no way to cross-reference across projects. And your notes live somewhere else entirely, disconnected from the work that generated them.

There's also a privacy ceiling: persistent AI memory requires your data on their servers. There's no path to keeping your context private with hosted tools.

## 💡 The solution

This system treats your projects as the primary artifact — decisions, notes, and reasoning accumulate as a byproduct of doing the work, not as a separate chore. Plain Markdown in version control as the durable layer, with an AI coding assistant as the intelligence layer. Four behaviors make this real:

- **Personal and project context** — your profile, past feedback, and current project state load before you type the first message
- **Memory proposals** — decisions worth keeping get flagged; you confirm, and they persist as versioned files
- **Capture proposals** — knowledge worth keeping beyond this project gets surfaced and stored
- **Note retrieval** — relevant notes come back when you need them

See [docs/claude-integration.md](docs/claude-integration.md) for the full detail on each behavior.

## ✨ What makes this different

**You keep everything.** Every document, note, decision, and conversation transcript is plain Markdown — searchable, version-controlled, readable in any text editor, and yours to build on.

**AI memory you can read and correct.** Not a black box — memory lives in files you can open, edit, and version like any other note. Projects start with a `_memory.md` that captures decisions, constraints, and what was rejected. When reasoning history gets long, it splits into a `decisions/` folder of atomic notes.

**You choose where your data goes.** Start with a frontier model for the best reasoning. Move to an open-weights model on your own machine when privacy matters. Hooks are plain Python scripts and notes are plain Markdown — the AI tool is a choice, not load-bearing infrastructure.

**The system proves itself.** The architecture, requirements, decisions, and tests behind this framework live inside it — the most complex project in the vault, maintained using the same hooks, memory, and commands you use for your own work.

For technical detail on context injection and automation boundaries, see [docs/claude-integration.md](docs/claude-integration.md) and [architecture.md](personal/projects/second-brain-setup/architecture.md).

## ⚖️ How this compares

|                                | Cloud AI (Claude, ChatGPT) | Obsidian standalone | Tier 1 (cloud) | Tier 2/3 (local) |
| ------------------------------ | -------------------------- | ------------------- | -------------- | ---------------- |
| AI context per session         | built-in                   | —                   | ✓              | ✓                |
| Automatic memory               | ✓ (no action needed)       | —                   | —              | —                |
| Memory — user-owned, versioned | —                          | —                   | ✓              | ✓                |
| Active capture                 | —                          | —                   | ✓ `/distill`   | ✓ `/distill`     |
| Active retrieval               | —                          | —                   | —              | ✓ RAG            |
| AI sees your content           | ✓                          | —                   | ✓ (Anthropic)  | —                |
| Local files / ownership        | —                          | ✓                   | ✓              | ✓                |
| Version control                | —                          | plugin needed       | ✓              | ✓                |
| Output files versioned         | —                          | —                   | ✓              | ✓                |
| Cross-project awareness        | —                          | —                   | ✓              | ✓                |
| Works offline                  | —                          | ✓                   | —              | ✓                |
| Data stays on machine          | —                          | ✓                   | —              | ✓                |
| Setup complexity               | none                       | low                 | medium         | high             |

*For known limitations and planned improvements, see [limitations-and-roadmap.md](docs/limitations-and-roadmap.md).*

## 🚀 Deployment tiers

Tier 1 is the fastest path to get started. Tier 2/3 is the path when data privacy is a requirement — same memory and context system, local inference instead of cloud.

| Tier | Name | Git hosting | AI inference | Hardware required |
| ---- | ---- | ----------- | ------------ | ----------------- |
| 1 | Cloud | GitHub | Claude Code → Anthropic API | None |
| 2 | Private cloud | Gitea on VPS | Claude Code → LiteLLM → Ollama (VPS) | None (VPS subscription) |
| 3 | Self-hosted | Gitea on own hardware | Claude Code → LiteLLM → Ollama (own hardware) | Own hardware + GPU |

See [docs/getting-started.md](docs/getting-started.md) for setup and [PRIVACY.md](PRIVACY.md) for data handling at each tier.

## ➕ Optional services

Optional services layer on top of any tier — configure what you need, skip what you don't. All configure via `.env` and degrade gracefully when absent.

| Service | What it adds | Tier |
|---|---|---|
| RAG (Ollama + Qdrant) | Semantic search; passive note surfacing during sessions | 2/3 |
| ntfy | Push notifications — CI failures, service health, unprocessed events | Any |
| Vikunja | Task sync — next actions from memory files synced to a task board | Any |
| LiteLLM | Local LLM inference — routes Claude Code to a private Ollama instance | 2/3 |

See [docs/configuration.md](docs/configuration.md) for setup instructions and all configuration variables.

## ⚡ Slash commands

Invoked by typing `/command-name` in a Claude Code session. Defined as Markdown files in `.claude/commands/` — no registration required.

| Command | When | What |
|---|---|---|
| `/init` | Starting something new | Initialize a project, area, or resource — asks your goal and inputs, proposes a classification, creates files (dashboard auto-generated by CI) |
| `/remember` | End of session | Judgment pass over current conversation — persists 🧠 project memory, 👤 profile updates, and ✅ task targets |
| `/distill` | Periodically | Process 🗂️ markers from current conversation into durable `resources/` notes |
| `/maintain` | Periodically | Vault operations — inbox processing, event processing, memory maintenance, resource note maintenance, reports |
| `/sync` | When committing | Git commit with Claude-drafted message + push |
| `/search` | Anytime | Query vault by meaning (Tier 2/3) or keyword (Tier 1) |
| `/contribute` | When improving | Package framework changes → PR to upstream |

See [docs/claude-integration.md](docs/claude-integration.md) for full command descriptions.

## 🛠️ Tool roles

| Tool | Role |
| ---- | ---- |
| VS Code + Foam | Editing, AI agent, wikilink resolution, graph view in editor |
| Obsidian + obsidian-git | Reading, navigation, graph view, mobile (capture + read) |

Both tools read the same plain Markdown files. The wikilink conventions in this system are designed to work with both simultaneously.

## 📁 Structure

Each context follows the same PARA layout:

```
{context}/           ← personal/ | professional/ | public/
├── projects/        ← active work with a defined outcome and deadline
├── areas/           ← ongoing responsibilities with no end date
├── resources/       ← reference material and topics of interest
└── archive/         ← completed or inactive items
```

Special folders: `_conversations/`, `_daily/`, `_inbox/`, `_infrastructure/`, `_scripts/`, `_templates/`

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full repository layout.

## ⚡ Quick start

**Start here — cloud path:** VS Code, Claude Code extension, Python 3.8+

1. Use this repo as a GitHub template → clone your fork
2. Run setup: `bash _scripts/setup.sh` (macOS/Linux) or
   `powershell -File _scripts/setup.ps1` (Windows)
3. Open `CLAUDE.md` and fill in the `{your-name}` placeholder
4. Start a session — the system is pre-configured and ready to use

**Add later — Tier 2/3 (private inference):** [LiteLLM](https://litellm.ai), [Ollama](https://ollama.com), self-hosted Gitea (Tier 2: VPS · Tier 3: own hardware)

See [docs/getting-started.md](docs/getting-started.md) for the full walkthrough and model recommendations.

## 🤝 Contributing

This framework is built to be used and improved. If you fork it and build something better — a script, a hook, a template, a workflow improvement — the path back upstream is already set up.

**GitHub template:** Fork or use this repo as a template to start your own instance. Your notes never leave your machine; only framework changes travel upstream.

**`/contribute`:** The slash command packages your framework-path changes into a branch and prepares a PR description — no manual cherry-picking or content-filtering required.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow, content safety guarantees, and how to report bugs or suggest improvements. For system architecture and component interfaces, see [architecture.md](personal/projects/second-brain-setup/architecture.md).

## 🙏 Prior art and influences

- [PARA method](https://fortelabs.com/blog/para/) — Tiago Forte
- [Obsidian](https://obsidian.md) — reading, navigation, and mobile layer
- [obsidian-git](https://github.com/Vinzent03/obsidian-git) — git sync for mobile
- [Foam](https://foambubble.github.io/foam/) — VS Code wikilink and graph extension
- [LiteLLM](https://litellm.ai) — LLM gateway (Anthropic API → Ollama translation layer)
- [Ollama](https://ollama.com) — local LLM runtime
