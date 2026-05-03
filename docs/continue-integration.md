# 🤖 Continue.dev Integration (local-first path)

How Continue.dev fits into this second brain — instruction files, context management, Ollama setup, and where judgment replaces automation. For the cloud path, see [claude-integration.md](claude-integration.md).

> Nothing leaves your machine. No API key required.


## 🦙 Setting up Ollama

[Ollama](https://ollama.com) runs LLMs locally. If you are on Tier 2 (self-hosted setup), Ollama is already running via Docker — see [self-hosted-setup.md](self-hosted-setup.md). Otherwise, install it natively and pull a model:

```bash
# For most hardware (recommended starting point)
ollama pull qwen2.5:7b

# For better reasoning quality if you have 16GB+ RAM
ollama pull qwen2.5:32b

# For note management tasks (not coding), a general model works well
# Coding-specific models are not required
```

Ollama runs as a local server at `http://localhost:11434`. No API key needed.


## ⚙️ Configuring Continue.dev to use Ollama

1. Open VS Code and click the Continue.dev icon in the sidebar
2. Open the Continue.dev config file (`~/.continue/config.json`)
3. Add your Ollama model as a provider:

```json
{
  "models": [
    {
      "title": "Qwen 2.5 7B (local)",
      "provider": "ollama",
      "model": "qwen2.5:7b",
      "apiBase": "http://localhost:11434"
    }
  ]
}
```

Continue.dev will now route all requests to your local Ollama instance — nothing leaves your machine.


## 🗂️ Project context in Continue.dev

Claude Code uses hook scripts to inject context automatically at session start. In Continue.dev, context loading is handled by slash commands instead — the same mechanism as all other commands in this system.

Use `/load-context` at the start of a session to load your profile, rules, and project files:

```
/load-context my-project
```

This loads `CLAUDE.md` (root), `_self/about.md`, `_self/rules.md`, and the project's `CLAUDE.md` and `_memory.md` — equivalent to what the four Claude Code hooks inject automatically.

You can also load context manually using Continue.dev's `@file` mentions for individual files.


## 💰 Context budget

Continue.dev's context window is determined by the model you're using — typically 32K–128K tokens depending on the model, which is much larger than Claude Code's per-hook limit.

`_memory.md` files may contain an `<!-- extended -->` marker. Keep summary sections above the marker and detailed history below — this keeps loaded context useful without overloading it.


## ⚡ Slash commands

Continue.dev supports native slash commands via `.continue/prompts/` — the same pattern as Claude Code's `.claude/commands/`. Every Claude Code slash command has a Continue.dev equivalent:

| Command | Claude Code | Continue.dev |
|---|---|---|
| `/sync-memory` | `.claude/commands/sync-memory.md` | `.continue/prompts/sync-memory.md` |
| `/commit` | `.claude/commands/commit.md` | `.continue/prompts/commit.md` |
| `/housekeeping` | `.claude/commands/housekeeping.md` | `.continue/prompts/housekeeping.md` |
| `/audit` | `.claude/commands/audit.md` | `.continue/prompts/audit.md` |
| `/review-memory` | `.claude/commands/review-memory.md` | `.continue/prompts/review-memory.md` |

The invocation is the same in both tools — type `/command-name` in the chat panel.


## 🌱 How `_self/` files grow

**`_self/about.md`** — the agent maintains this across sessions via `/sync-memory`. Growth policy:

- New behavioral observations are **merged into existing bullets** rather than appended
- When the `## Reflection` section exceeds ~20 bullets, `/sync-memory` re-clusters them into labeled sub-groups

**`_self/rules.md`** — grows from corrections and confirmed preferences, not observations. The agent saves a rule when you correct an approach ("don't do X") or explicitly confirm a non-obvious one ("yes, keep doing that"). Rules are never appended automatically — they require an explicit signal from you.

## ⚖️ The judgment / automation line

The same principle applies regardless of which agent you use:

| Agent | Scripts |
|---|---|
| Commit message drafting | Git pull, commit, push |
| Project classification | Index file generation |
| Memory updates | Frontmatter field updates |

If a step requires no judgment, it's a script. If it does, it's the agent.


## 🔄 Claude Code as a parallel path

Both paths can be active simultaneously — the line is yours to draw based on content sensitivity. If you need capabilities not yet available in local models (complex multi-step reasoning, very long context synthesis), use Claude Code for that work. See [claude-integration.md](claude-integration.md). Be aware that Claude Code sends session context to Anthropic's API — read [PRIVACY.md](../PRIVACY.md).
