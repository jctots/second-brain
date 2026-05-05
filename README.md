# 🧠 second-brain

> "You do not rise to the level of your goals. You fall to the level of your systems."
> — James Clear

A platform for building with knowledge, not just storing it — plain markdown and
version control as the foundation, with an AI that thinks with you across sessions
and compounds what you learn into better work.

**The recursive part:** the system and the person using it improve together. `second-brain-setup` — the project that designs this second brain — lives as a meta project inside it. It doesn't just support self-improvement; it contains the mechanism of its own improvement — the loop closes on itself. The deeper loop is human: past reasoning informs present decisions, behavioral patterns surface across sessions, knowledge compounds instead of just accumulating. The AI is a multiplier, through the systems you build — but what it multiplies is you.

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
the intelligence layer operating against structured context. Four behaviors run
automatically:

**Automatic context** — at session start, your profile, behavioral feedback, and project
context (current state, open questions, past decisions) load via hook scripts. The AI
enters each session already knowing who you are and what you're working on — no
manual copy-paste, no re-explaining.

**Automatic memory** — at session end, `/remember` persists decisions, project state,
and behavioral corrections to the right files. What the AI learns in one session is
available in the next.

**Automatic capture** — during sessions, the AI identifies topics worth keeping as
reference material and queues them as draft note proposals. Run `/distill` to review
each proposal interactively — refine, confirm, or skip. Notes accumulate because the
system noticed them, not because you remembered to write them.

**Automatic retrieval** — knowledge comes back two ways: relevant notes surface
automatically via retrieval-augmented generation (RAG), and you can ask the agent
directly — "what do I know about X?" — and it searches and synthesizes from your
vault on demand. Passive surfacing and active query, both in the same session.

See `docs/claude-integration.md` for the full technical detail.

## 🧠 Why "second brain"?

The name comes from a simple idea: an external system that remembers so your brain
doesn't have to. This system takes that further — comprehensive capture, not a curated
highlight reel. Everything you think, decide, and learn has a place here.

But storage alone doesn't make it a second brain. A second brain builds. The four
behaviors above make this real: capture feeds your projects; retrieval brings past
reasoning back — automatically or on demand; memory means the AI grows with you
across sessions. Notes aren't the output — they're raw material. What you build with
them is the point.

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

**AI-proposed capture via `/distill`.** During every session, the AI surfaces reference
material candidates and queues them for review. You decide what stays — the system
does the noticing.

**Agent-agnostic structure.** Hooks are plain Python scripts and notes are plain
Markdown. The AI tool is a choice, not load-bearing infrastructure.

## ⚖️ How this compares

|                         | Cloud AI (Claude, ChatGPT) | Obsidian standalone | This setup            |
| ----------------------- | -------------------------- | ------------------- | --------------------- |
| AI context per session  | built-in                   | —                   | via instruction files |
| Active capture          | —                          | —                   | ✓ `/distill`          |
| Active retrieval        | —                          | —                   | ✓ RAG + agent query   |
| Local files / ownership | —                          | ✓                   | ✓                     |
| Version control         | —                          | plugin needed       | ✓ git-native          |
| Output files versioned  | —                          | —                   | ✓                     |
| Cross-project awareness | —                          | —                   | ✓ by design           |
| Works offline           | —                          | ✓                   | ✓ (local LLM path)    |
| Data stays on machine   | —                          | ✓                   | ✓ (local LLM path)    |
| Setup complexity        | none                       | low                 | medium                |

## 🚀 Deployment tiers

Three tiers built from the same framework. Start at Tier 1 — add tiers as your privacy needs grow.

| Tier | Name | Git hosting | AI inference | Hardware required |
| ---- | ---- | ----------- | ------------ | ----------------- |
| 1 | Cloud | GitHub | Claude Code → Anthropic API | None |
| 2 | Private cloud | Gitea on VPS | Claude Code → LiteLLM → Ollama (VPS) | None (VPS subscription) |
| 3 | Self-hosted | Gitea on own hardware | Claude Code → LiteLLM → Ollama (own hardware) | Own hardware + GPU |

**Same tool across all tiers.** Claude Code is the AI interface at every tier. What changes is where inference happens — set `ANTHROPIC_BASE_URL` to point at a LiteLLM gateway for Tier 2/3, unset it to return to Anthropic. Hooks, slash commands, context injection, and conversation saving work identically at every tier.

**Tier 1 — Cloud.** GitHub template → clone → run setup → start. No infrastructure. Suitable for: framework evaluation, non-sensitive content, public notes. Privacy caveat: files Claude Code reads are sent to Anthropic's API — keep that boundary intentional.

**Tier 2 — Private cloud.** Gitea on a VPS (content host and CI runner). LiteLLM + Ollama on the same VPS. Claude Code routes through LiteLLM instead of Anthropic — no local GPU required. Suitable for: sensitive content without homelab hardware. Privacy: inference stays on user-controlled infrastructure.

**Tier 3 — Self-hosted.** Gitea, LiteLLM, and Ollama all on user-owned hardware. No data leaves user-owned infrastructure. Suitable for: comprehensive capture of personal, professional, and sensitive content with maximum sovereignty.

See `docs/getting-started.md` for setup instructions. See `docs/self-hosted-setup.md` for Tier 2/3 infrastructure detail (Docker Compose, Gitea, Gitea Actions runner, vault migration).

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

**Add later — Tier 2/3 (private inference):** [LiteLLM](https://litellm.ai),
[Ollama](https://ollama.com), self-hosted Gitea (Tier 2: VPS · Tier 3: own hardware)

See `docs/getting-started.md` for the full walkthrough and model recommendations.

## 🙏 Prior art and influences

- [PARA method](https://fortelabs.com/blog/para/) — Tiago Forte
- [Obsidian](https://obsidian.md) — reading, navigation, and mobile layer
- [obsidian-git](https://github.com/Vinzent03/obsidian-git) — git sync for mobile
- [Foam](https://foambubble.github.io/foam/) — VS Code wikilink and graph extension
- [LiteLLM](https://litellm.ai) — LLM gateway (Anthropic API → Ollama translation layer)
- [Ollama](https://ollama.com) — local LLM runtime

The goal was never better notes. It was better work — and a system smart enough to make you better at what you do.
