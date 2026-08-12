# 🚀 Getting Started

How to fork this template and set up your own AI-assisted second brain. Start with Claude Code + GitHub — no local infrastructure needed. Add private inference (Tier 2 or Tier 3) when you're ready to capture sensitive content without sending it to Anthropic.


## 🏗️ Deployment tiers

| | Tier 1 — Cloud | Tier 2 — Private cloud | Tier 3 — Self-hosted |
|---|---|---|---|
| Git host | GitHub | Gitea on VPS | Gitea on own hardware |
| AI inference | Anthropic API | LiteLLM + Ollama (VPS) | LiteLLM + Ollama (own hardware) |
| Semantic search | Keyword only | Qdrant + embedding model (VPS) | Qdrant + embedding model (own hardware) |
| Framework CI | GitHub Actions | GitHub Actions | GitHub Actions |
| Content CI | — | Gitea Actions | Gitea Actions |
| Hardware required | None | VPS (GPU recommended) | Own hardware + GPU (recommended) |
| Data sovereignty | Partial | Inference on user-controlled infra | Full |

Claude Code is the AI interface at every tier — only `ANTHROPIC_BASE_URL` changes. Steps 1–7 below cover Tier 1. See [private-cloud-setup.md](private-cloud-setup.md) for Tier 2 and [self-hosted-setup.md](self-hosted-setup.md) for Tier 3.


## 📋 Prerequisites

| Tool | Path | Notes |
|---|---|---|
| VS Code | Both | Primary editing environment |
| Python 3.8+ | Both | For hook scripts and automation |
| [Obsidian](https://obsidian.md) | Both (recommended) | Reading, navigation, graph view, and mobile access |
| [Foam extension](https://marketplace.visualstudio.com/items?itemName=foam.foam-vscode) | Both (recommended) | VS Code wikilink resolution and graph view |
| [Claude Code extension](https://marketplace.visualstudio.com/items?itemName=Anthropic.claude-code) | All tiers | AI agent — Anthropic API (Tier 1) or LiteLLM gateway (Tier 2/3) |
| [LiteLLM](https://litellm.ai) | Tier 2/3 | Gateway that translates Claude Code's API format to Ollama |
| [Ollama](https://ollama.com) | Tier 2/3 | Local LLM runtime |


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
- Reads [`_infrastructure/stack.yaml`](../_infrastructure/stack.yaml) for the list of required VS Code extensions and installs them
- Configures the save-conversation hook in VS Code settings


## ☁️ Step 3: Sign in to Claude Code

Open the Claude Code panel in VS Code (sidebar icon). Follow the sign-in prompts — it will open a browser to authenticate with your Anthropic account.

This connects to Anthropic's API (Tier 1). To switch to private inference later, set `ANTHROPIC_BASE_URL` to a LiteLLM gateway — see [private-cloud-setup.md](private-cloud-setup.md) or [self-hosted-setup.md](self-hosted-setup.md).


## 🦙 Step 4: Pull a model (Tier 2/3 only)

Skip this step if staying on Tier 1.

Once your LiteLLM + Ollama stack is running (see the tier setup docs), pull a model:

```bash
# For most hardware — good balance of quality and speed
ollama pull qwen2.5:7b

# For better reasoning if your hardware supports it
ollama pull qwen2.5:32b
```

For GPU hardware, larger models (`qwen2.5:32b`) give better reasoning quality. Without a GPU, 7B models are the practical ceiling for reasonable response times.


## 👤 Step 5: Create your profile

Create `_self/about.md`. This file is where the AI will maintain a profile and behavioral reflection about you across sessions. Start minimal — it will populate over time:

```markdown
# About {your-name}

## Profile

_AI-maintained. Updated via /remember._

## Reflection

_AI-maintained. Updated via /remember._
```


## 📁 Step 6: Start with the pre-seeded setup project

The template includes a ready-to-use project for maintaining your second brain itself:

```
personal/projects/second-brain-setup/
├── CLAUDE.md           ← project instructions
├── _memory.md          ← AI-maintained current state and decisions
├── index.md            ← project overview
├── decisions/          ← your design history, one atomic note per decision
├── requirements.md     ← system requirements
├── architecture.md     ← system structure and component interfaces
└── roadmap.md          ← improvement backlog
```

Open `decisions/index.md` to see your first decision pre-seeded. Open the linked decision file and replace the `{YYYY-MM-DD}` placeholder with today's date.

When you want additional projects, create them under the appropriate context and copy from the templates:

```
personal/projects/my-project/
├── CLAUDE.md        ← copy from _templates/CLAUDE-template.md
├── _memory.md       ← copy from _templates/_memory-template.md
├── index.md         ← copy from _templates/index-template.md
└── reference.md     ← copy from _templates/reference-template.md
```


## 💬 Step 7: Start a conversation

Open VS Code, open the Claude Code extension, and start a session. Reference your project in the first message — the hook scripts inject context automatically (profile, rules, project `CLAUDE.md` and `_memory.md`).

The hook announcement at session start confirms what was loaded:
> *"Loaded: `personal/projects/my-project/CLAUDE.md` + `_memory.md`"*

No announcement = hook miss. See [docs/claude-integration.md](claude-integration.md) for the full hook architecture and slash command reference.


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

**Keep project instruction files under ~9,000 characters each.** Claude Code caps a hook's whole output at 10,000 chars — per hook invocation, not per file, so a turn touching two projects shares one budget. Files over the target still load; once the budget runs out, the injector swaps the remainder for a pointer line telling Claude to read the file itself. See [claude-integration.md](claude-integration.md) for details.

**Name your project folders with kebab-case.** Easier to detect from natural language in your first message.

**Run `/remember` at the end of sessions with significant decisions.** This is what keeps `_memory.md` useful — without it, context is lost between sessions.


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

