# 🚀 Getting Started

How to fork this template and set up your own AI-assisted second brain. Start with Claude Code + GitHub — no local infrastructure needed. Add Continue.dev + Ollama alongside it when you need local-first processing for sensitive content.


## 🏗️ Deployment tiers

This system supports two deployment tiers. Most users start with Tier 1 and add Tier 2 when they're ready to capture sensitive content privately.

| | Tier 1 — Evaluation | Tier 2 — Full private |
|---|---|---|
| Git host | GitHub | Gitea (self-hosted) |
| AI | Claude Code | Continue.dev + Ollama |
| Framework CI | GitHub Actions | GitHub Actions |
| Content CI | — | Gitea Actions |
| Data sovereignty | Partial | Full |

Steps 1–7 walk through the initial setup for both tiers — path-specific steps are labelled. See [self-hosted-setup.md](self-hosted-setup.md) for the Tier 2 infrastructure.


## 📋 Prerequisites

| Tool | Path | Notes |
|---|---|---|
| VS Code | Both | Primary editing environment |
| Python 3.8+ | Both | For hook scripts and automation |
| [Obsidian](https://obsidian.md) | Both (recommended) | Reading, navigation, graph view, and mobile access |
| [Foam extension](https://marketplace.visualstudio.com/items?itemName=foam.foam-vscode) | Both (recommended) | VS Code wikilink resolution and graph view |
| [Claude Code extension](https://marketplace.visualstudio.com/items?itemName=Anthropic.claude-code) | Cloud path | AI agent via Anthropic API |
| [Continue.dev extension](https://marketplace.visualstudio.com/items?itemName=Continue.continue) | Local-first path | AI agent, runs locally via Ollama |
| [Ollama](https://ollama.com) | Local-first path | Local LLM runtime — nothing leaves your machine |


## 🍴 Step 1: Fork and clone

Use this repo as a GitHub template:

1. Click **Use this template** on GitHub
2. Name your repo (e.g., `second-brain` or `notes`)
3. Clone it locally:
   ```bash
   git clone https://github.com/your-username/your-repo-name
   cd your-repo-name
   ```

> **Adding this as upstream to an existing repo?** Add the `merge=ours` rule to your `.gitattributes` before the first merge — otherwise the upstream `.gitignore` will overwrite yours:
> ```
> .gitignore merge=ours
> ```
> Forks created from the template already have this rule included.


## ⚙️ Step 2: Run setup

The setup scripts install VS Code extensions and configure hooks.

**macOS / Linux:**
```bash
bash _scripts/setup.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File _scripts/setup.ps1
```

What setup does:
- Reads `infra.yaml` for the list of required VS Code extensions and installs them
- Configures the save-conversation hook in VS Code settings


## ☁️ Step 3: Sign in to Claude Code (cloud path only)

Skip this step if you are starting with Continue.dev + Ollama.

Open the Claude Code panel in VS Code (sidebar icon). Follow the sign-in prompts — it will open a browser to authenticate with your Anthropic account.


## 🦙 Step 4: Pull a model (local-first path only)

Skip this step if you are starting with Claude Code.

Pull a model via Ollama. For note management tasks (not coding), a smaller reasoning model is sufficient:

```bash
ollama pull qwen2.5:7b
```

For a larger, more capable model if your hardware supports it:

```bash
ollama pull qwen2.5:32b
```

See [docs/continue-integration.md](continue-integration.md) for model recommendations and how to configure Continue.dev to use Ollama.


## 👤 Step 5: Create your profile

Create `_self/about.md`. This file is where the AI will maintain a profile and behavioral reflection about you across sessions. Start minimal — it will populate over time:

```markdown
# About {your-name}

## Profile

_AI-maintained. Updated via /sync-memory._

## Reflection

_AI-maintained. Updated via /sync-memory._
```


## 📁 Step 6: Start with the pre-seeded setup project

The template includes a ready-to-use project for maintaining your second brain itself:

```
personal/projects/second-brain-setup/
├── CLAUDE.md           ← project instructions
├── _memory.md          ← AI-maintained current state and decisions
├── index.md            ← project overview
├── decisions.md        ← your design history, pre-seeded with one entry
├── requirements.md     ← system requirements
├── architecture.md     ← system structure and component interfaces
└── roadmap.md          ← improvement backlog
```

Open `decisions.md` and replace the `{YYYY-MM-DD}` placeholder with today's date. That's your first decision recorded — adopting this template and why.

When you want additional projects, create them under the appropriate context and copy from the templates:

```
personal/projects/my-project/
├── CLAUDE.md        ← copy from _templates/CLAUDE-template.md
├── _memory.md       ← copy from _templates/_memory-template.md
├── index.md         ← copy from _templates/index-template.md
└── reference.md     ← copy from _templates/reference-template.md
```


## 💬 Step 7: Start a conversation

**Cloud path (Claude Code):** Open VS Code, open the Claude Code extension, and start a session. Reference your project in the first message — the hook scripts inject context automatically. See [docs/claude-integration.md](claude-integration.md) for the full hook architecture.

**Local-first path (Continue.dev):** Open VS Code, open the Continue.dev sidebar, and start a session. Reference your project and instruction files explicitly in the first message — context is not injected automatically. See [docs/continue-integration.md](continue-integration.md) for context loading patterns.


## 🗂️ Folder structure you'll build out

```
your-repo/
├── personal/
│   ├── projects/
│   │   └── second-brain-setup/  ← pre-seeded, start here
│   ├── areas/          ← ongoing responsibilities
│   ├── resources/      ← reference material
│   └── archive/        ← completed/inactive items
├── professional/       ← same PARA structure, private
├── public/             ← same PARA structure, publishable
├── _inbox/             ← capture zone, process and move out
├── _daily/             ← daily notes (YYYY-MM-DD.md)
├── _conversations/     ← saved sessions
├── _self/
│   └── about.md        ← AI-maintained profile
└── _templates/         ← note templates
```


## 💡 Tips

**Keep project instruction files under ~3,000 characters combined with `_memory.md`.** Context has a budget — large files may be silently truncated. See [continue-integration.md](continue-integration.md) for details.

**Name your project folders with kebab-case.** Easier to detect from natural language in your first message.

**Run `/sync-memory` at the end of sessions with significant decisions.** This is what keeps `_memory.md` useful — without it, context is lost between sessions. (Claude Code path only — see [continue-integration.md](continue-integration.md) for the Continue.dev equivalent.)


## 📱 Obsidian for reading and mobile

This system is designed for two complementary tools: VS Code + Foam for editing and AI, Obsidian for reading, navigation, and mobile. Both read the same plain Markdown files — the wikilink conventions are designed to work with both simultaneously.

**Desktop:** Open your vault folder in Obsidian. Graph view, backlinks, and click-to-navigate work out of the box.

**Mobile (reading + capture):**
1. Install [Obsidian](https://obsidian.md) on iOS or Android
2. Install the [obsidian-git plugin](https://github.com/Vinzent03/obsidian-git) from the Obsidian community plugins
3. Generate an SSH key or personal access token for your git host
4. Configure obsidian-git to point at your repo — it syncs on open/close
5. Your vault is now readable on your phone; drop notes into `_inbox/` for later processing in VS Code

obsidian-git supports GitHub, Gitea, Forgejo, and any other git host over SSH or HTTPS.

**Wikilink compatibility:** Foam resolves `[[folder-name]]` to `index.md` automatically. Obsidian does not — use `[[folder/index|display]]` for folder entry points to keep both tools happy. See `requirements.md` in `personal/projects/second-brain-setup/` for the full convention.

