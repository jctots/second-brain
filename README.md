# 🧠 second-brain

> "You do not rise to the level of your goals. You fall to the level of your systems."
> — James Clear

A PARA-based personal knowledge system built on plain markdown and version control,
with AI-augmented workflows that keep your notes portable and your content private.

**The recursive part:** the author's own instance is a fork of this repository —
maintained using the same system it describes. The design decisions, project tracking,
and improvement workflow all live inside that private instance. What you're reading is
maintained from the inside: live evidence that the architecture works, not a
retrospective write-up.

## 🔍 The problem

The typical PKM path — Obsidian with a plugin ecosystem — compounds friction quickly.
More time configuring templates and rules than writing notes. Plugin-specific markup
makes files unreadable outside the app. Portability is gone.

AI chat tools (Claude.ai Projects, ChatGPT) have the right scoped context model, but
three things are missing: you can't version anything — not your instructions, not your
memory, and not the output files the AI produces for you (the documents, drafts, and
analyses that are the actual value); you can't cross-reference information across
projects; you have no offline copy of your work.

## 💡 The solution

Plain markdown in version control as the durable layer, with an AI coding assistant as
the intelligence layer operating against structured context.

Four files load automatically at session start across two layers:

| Layer   | File                   | Purpose                                              |
| ------- | ---------------------- | ---------------------------------------------------- |
| Vault   | `CLAUDE.md`            | Vault-wide conventions, structure, and rules         |
| User    | `_self/about.md`       | AI-maintained profile — who you are, how you work    |
| User    | `_self/rules.md`       | Feedback that persists across sessions               |
| Project | `{project}/CLAUDE.md`  | Instructions and constraints scoped to that project  |
| Project | `{project}/_memory.md` | AI-maintained running log of decisions and current state |

Root `CLAUDE.md` is loaded by Claude Code natively. The other four load via hook scripts at session start.

The AI enters each session with full context already loaded — no manual copy-paste,
no re-explaining. This is the same pattern Anthropic's
[Model Context Protocol](https://modelcontextprotocol.io) formalizes; this system
implements it directly in the filesystem.

## ✨ What makes this different

**AI context injection with an explicit budget.** Instruction files have a hard limit on
what gets loaded per session. This system manages that budget deliberately: separate
files for profile vs. project context, a per-file size limit enforced at write time, and
an `<!-- extended -->` delimiter in `_memory.md` to keep injected content bounded while
preserving full history on disk.

**Deterministic vs. judgment split.** Scripts handle git mechanics, index generation,
and file operations. The AI agent handles commit message drafting, project
classification, and content decisions. If something requires no judgment, it's a script.
If it does, it's the agent.

**Design rationale as a first-class artifact.** Projects start with a `_memory.md` that
captures why things are the way they are — decisions, constraints, what was rejected.
When reasoning history gets long, it splits into a dedicated `decisions.md`. The design
rationale for this system is published in `docs/`.

**Agent-agnostic structure.** Hooks are plain Python scripts and notes are plain
Markdown. The AI tool is a choice, not load-bearing infrastructure.

## ⚖️ How this compares

|                         | Cloud AI (Claude, ChatGPT) | Obsidian standalone | This setup            |
| ----------------------- | -------------------------- | ------------------- | --------------------- |
| AI context per session  | built-in                   | —                   | via instruction files |
| Local files / ownership | —                          | ✓                   | ✓                     |
| Version control         | —                          | plugin needed       | ✓ git-native          |
| Output files versioned  | —                          | —                   | ✓                     |
| Cross-project awareness | —                          | —                   | ✓ by design           |
| Works offline           | —                          | ✓                   | ✓ (local LLM path)    |
| Data stays on machine   | —                          | ✓                   | ✓ (local LLM path)    |
| Setup complexity        | none                       | low                 | medium                |

## 🚀 Deployment options

**New here?** Start with Claude Code + GitHub — no local infrastructure needed. Add the
local-first path alongside it when you're ready to capture sensitive content.

The AI tool choice is per task, not per setup:

| Content type                                          | AI tool               | Infrastructure |
| ----------------------------------------------------- | --------------------- | -------------- |
| Non-sensitive — public notes, framework, contributing | Claude Code           | GitHub         |
| Sensitive — personal, professional                    | Continue.dev + Ollama | Gitea          |

The line is yours to draw. `public/` content is typically safe for cloud AI; `personal/`
and `professional/` typically aren't. Framework files are non-sensitive by design.

**The pragmatic setup:** GitHub for the framework, Gitea for all content, Claude Code for
non-sensitive work, Continue.dev + Ollama for sensitive work — both paths active,
each used where appropriate.

The local-first path requires self-hosted infrastructure: Gitea (content host and CI
runner — Gitea Actions handles content-aware automation that cannot run on GitHub) and
Ollama (local models). Evaluate the setup and maintenance cost before committing.

See `docs/self-hosted-setup.md` for the full Tier 2 setup (Docker Compose, Gitea, Gitea Actions runner, vault migration).

Privacy caveat: any file Claude Code reads is sent to Anthropic's API. Keep that
boundary intentional.

See `docs/getting-started.md` for setup instructions for both paths.

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

Special folders: `_conversations/`, `_daily/`, `_inbox/`, `_scripts/`, `_templates/`

Projects are the natural entry point — areas and resources grow from active
project work as the agent surfaces opportunities to capture reference material.
You can add content anywhere directly, but you don't need to pre-populate
areas or resources to get started.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full repository layout.

## ⚡ Quick start

**Start here — cloud path:** VS Code, Claude Code extension, Python 3.8+

1. Use this repo as a GitHub template → clone your fork
2. Run setup: `bash _scripts/setup.sh` (macOS/Linux) or
   `powershell -File _scripts/setup.ps1` (Windows)
3. Open `CLAUDE.md` and fill in the `{your-name}` placeholder
4. Start a session — the system is pre-configured and ready to use

The included `second-brain-setup` project is the same meta-project used to maintain
this repository — the design decisions, improvement backlog, and session transcripts
that produced what you're reading live inside it. To see the system configure itself,
start a session with: *"project: second-brain-setup — help me personalize this setup"*
— the agent reads the project context and walks you through it. Or jump straight to
your own projects.

**Add later — local-first path:** VS Code, [Continue.dev extension](https://continue.dev),
[Ollama](https://ollama.com), Python 3.8+, self-hosted Gitea

See `docs/getting-started.md` for the full walkthrough and model recommendations.

## 🙏 Prior art and influences

- [PARA method](https://fortelabs.com/blog/para/) — Tiago Forte
- [Obsidian](https://obsidian.md) — reading, navigation, and mobile layer
- [obsidian-git](https://github.com/Vinzent03/obsidian-git) — git sync for mobile
- [Foam](https://foambubble.github.io/foam/) — VS Code wikilink and graph extension
- [Continue.dev](https://continue.dev) — open-source AI coding assistant (local-first path)
- [Ollama](https://ollama.com) — local LLM runtime

Build for the problem in front of you — that's how this one was built.
