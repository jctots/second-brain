# 🔒 Privacy

This document explains what data leaves your machine when using this system, what stays local, and how to control your exposure.


## 🏠 Your notes stay local

This system does not upload your vault to any server. Notes are plain Markdown files stored on your machine and in your own git repository. No background sync, no cloud storage, no third-party indexing.


## 🤖 Primary path: Continue.dev + Ollama (nothing leaves your machine)

The recommended setup uses Continue.dev (a VS Code extension) with Ollama running locally. In this configuration:

- The AI model runs entirely on your hardware
- No API calls are made to any external service
- Your notes, context files, and conversation history never leave your machine
- The only network activity is the initial model download via `ollama pull`

This is the right choice if your second brain contains personal, health, financial, professional, or any other sensitive content — which it probably does by design.


## ⚠️ Alternative path: Claude Code (data sent to Anthropic)

If you choose to use Claude Code instead of Continue.dev + Ollama, every session sends data to Anthropic's API. Specifically:

| What | When | Controlled by |
|---|---|---|
| Summary section of your profile file | Every session start (hook) | `<!-- extended -->` delimiter |
| Summary section of your rules/feedback file | Every session start (hook) | `<!-- extended -->` delimiter |
| Summary section of active project's instruction file | Every session start (hook) | `<!-- extended -->` delimiter |
| Summary section of active project's memory file | Every session start (hook) | `<!-- extended -->` delimiter |
| Messages you type and files you share manually | During the session | You |

**What does not get sent automatically:** the full vault, daily notes, inbox, archived projects, or any file below the `<!-- extended -->` delimiter in hook-injected files.

If you use Claude Code, you are accepting this tradeoff. See [docs/claude-integration.md](docs/claude-integration.md) for setup details and how to minimize exposure.


## 🎛️ Controlling what gets injected (Claude Code path)

The `<!-- extended -->` delimiter in hook-injected files marks the boundary between what gets sent and what stays local. Everything above the marker is injected; everything below is preserved in the file but never sent automatically.

Keep sensitive details — specific names, financial figures, health information — below the marker or in files that are never referenced as project context.


## 📜 Anthropic's data policy

Claude Code uses the Anthropic API. Anthropic's policy for API usage:

- **API inputs and outputs are not used to train models by default.** This applies to Claude Code sessions.
- Anthropic's full privacy policy: [anthropic.com/privacy](https://www.anthropic.com/privacy)
