# 🧠 second-brain

> "You do not rise to the level of your goals. You fall to the level of your systems."
> — James Clear

A platform for building with knowledge, not just storing it — plain markdown and
version control as the foundation, with an AI that thinks with you across sessions
and compounds what you learn into better work.

*What does AI compound when it works with you?*

## 🔍 The problem

The typical PKM path — Obsidian with a plugin ecosystem — compounds friction quickly.
More time configuring templates and rules than writing notes. Plugin-specific markup
makes files unreadable outside the app. Portability is gone.

AI chat tools (Claude.ai Projects, ChatGPT) have the right scoped context model, but
several things are missing: you can't version anything — not your instructions, not your
memory, and not the output files the AI produces for you (the documents, drafts, and
analyses that are the actual value); you can't cross-reference information across
projects; you have no offline copy of your work.

Insights slip through during sessions — you're deep in a problem, notice something
worth keeping, but stopping to write a note breaks your flow. And what you do capture
tends to stay buried: knowledge from three months ago doesn't find its way back when
it's relevant again. The vault becomes a write-only archive.

## 💡 The solution

Plain markdown in version control as the durable layer, with an AI coding assistant as
the intelligence layer operating against structured context. Four behaviors work together:

**Automatic context** — at session start, your profile, behavioral feedback, and project context load via hook scripts. The AI enters each session already knowing who you are and what you're working on. Claude Code reads `CLAUDE.md` files from the directory hierarchy by default — this system adds two things on top: a user profile layer (`_self/about.md`) with no Claude Code equivalent, and intent-based project detection — the right project context loads based on what you mention in your first message, not which folder you opened the terminal in. Context is budget-controlled: each injected file has an enforced size limit so injection cost stays predictable.

**AI-proposed memory** — during sessions, the AI emits 🧠 markers when a decision or project state change is worth keeping, 👤 markers when a behavioral pattern or profile fact surfaces, and ✅ markers when a next action surfaces. At session end, `/remember` makes a judgment pass over the full conversation — you confirm what stays. Memory lives in the vault as plain Markdown: version-controlled, visible in your note editor, and portable across AI tools. This is a deliberate trade-off against the fully-automatic memory built into Claude Code — you keep editorial control and ownership of what gets persisted.

**AI-proposed capture** — during sessions, the AI emits 🗂️ markers when something has lasting reference value beyond the current project. Run `/distill` to review proposals — confirm, refine, or skip. Notes accumulate because the system noticed them, not because you remembered to stop and write them.

**Retrieval** — relevant note titles surface automatically each turn via RAG. The AI emits a `📖` marker when full content is worth loading — retrieved on the next turn. Ask on demand with `/search "topic"` — semantic search (Tier 2/3) or keyword (Tier 1). RAG also powers automatic project context injection and duplicate detection during `/distill`.

See [docs/claude-integration.md](docs/claude-integration.md) for the full technical detail.

## 🧠 Why "second brain"?

Storage alone doesn't make it a second brain — a second brain builds. The four behaviors above make this real: capture feeds your projects; retrieval brings past reasoning back; memory means the AI grows with you across sessions. Notes aren't the output — they're raw material. What you build with them is the point.

## ✨ What makes this different

**Context injection with an explicit budget.** Each injected file has a hard size limit — profile, rules, and project context are separate hooks with independent budgets. Truncation is silent; the system manages it deliberately. See [docs/claude-integration.md](docs/claude-integration.md).

**Deterministic vs. judgment split.** Scripts handle git mechanics, index generation, and file operations. The AI handles commit message drafting, project classification, and memory updates. If a step requires no judgment, it's a script.

**Design rationale as a first-class artifact.** Projects start with a `_memory.md` that captures decisions, constraints, and what was rejected. When reasoning history gets long, it splits into a `decisions/` folder of atomic notes. The design rationale for this system is captured in [[second-brain-setup/decisions/index|decisions/]] in the second-brain-setup project — the project that designs and maintains the framework itself.

**Agent-agnostic structure.** Hooks are plain Python scripts and notes are plain Markdown. The AI tool is a choice, not load-bearing infrastructure.

**Self-improving by design.** The project that designs and maintains this system lives inside it — using the same hooks, memory, and commands it documents. The system improves itself.

## ⚖️ How this compares

|                         | Cloud AI (Claude, ChatGPT) | Obsidian standalone | This setup            |
| ----------------------- | -------------------------- | ------------------- | --------------------- |
| AI context per session  | built-in                   | —                   | via instruction files |
| Automatic memory        | ✓ (no action needed)       | —                   | —                     |
| Memory — user-owned, versioned | —                   | —                   | ✓                     |
| Active capture          | —                          | —                   | ✓ `/distill`          |
| Active retrieval        | —                          | —                   | ✓ RAG + agent query   |
| Local files / ownership | —                          | ✓                   | ✓                     |
| Version control         | —                          | plugin needed       | ✓ git-native          |
| Output files versioned  | —                          | —                   | ✓                     |
| Cross-project awareness | —                          | —                   | ✓ by design           |
| Works offline           | —                          | ✓                   | ✓ (local LLM path)    |
| Data stays on machine   | —                          | ✓                   | ✓ (local LLM path)    |
| Setup complexity        | none                       | low                 | medium                |

*For known limitations and planned improvements, see [evolution.md](docs/evolution.md).*

## 🚀 Deployment tiers

Three tiers built from the same framework. Start at Tier 1 — add tiers as your privacy requirements grow.

| Tier | Name | Git hosting | AI inference | Hardware required |
| ---- | ---- | ----------- | ------------ | ----------------- |
| 1 | Cloud | GitHub | Claude Code → Anthropic API | None |
| 2 | Private cloud | Gitea on VPS | Claude Code → LiteLLM → Ollama (VPS) | None (VPS subscription) |
| 3 | Self-hosted | Gitea on own hardware | Claude Code → LiteLLM → Ollama (own hardware) | Own hardware + GPU |

See [docs/getting-started.md](docs/getting-started.md) for setup and [PRIVACY.md](PRIVACY.md) for data handling at each tier.

## ⚡ Slash commands

Invoked by typing `/command-name` in a Claude Code session. Defined as Markdown files in `.claude/commands/` — no registration required.

| Command | When | What |
|---|---|---|
| `/remember` | End of session | Judgment pass over current conversation — persists 🧠 project memory, 👤 profile updates, and ✅ task targets |
| `/distill` | Periodically | Process 🗂️ markers from current conversation into durable `resources/` notes |
| `/maintain` | Periodically | Vault health audit — artifacts, pending events, reports, reviews |
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

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow, content safety guarantees, and how to report bugs or suggest improvements. For system architecture and component interfaces, see [second-brain-setup/architecture.md](personal/projects/second-brain-setup/architecture.md).


## 🙏 Prior art and influences

- [PARA method](https://fortelabs.com/blog/para/) — Tiago Forte
- [Obsidian](https://obsidian.md) — reading, navigation, and mobile layer
- [obsidian-git](https://github.com/Vinzent03/obsidian-git) — git sync for mobile
- [Foam](https://foambubble.github.io/foam/) — VS Code wikilink and graph extension
- [LiteLLM](https://litellm.ai) — LLM gateway (Anthropic API → Ollama translation layer)
- [Ollama](https://ollama.com) — local LLM runtime

**The systems you build determine what AI multiplies — make sure it's you.**
