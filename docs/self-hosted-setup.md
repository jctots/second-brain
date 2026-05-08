# 🏠 Self-Hosted Setup (Tier 3)

How to add Gitea, LiteLLM, and Ollama on your own hardware alongside your existing GitHub + Claude Code setup. Tier 3 gives you full data sovereignty — your notes are hosted on hardware you own, your LLM runs on your own infrastructure, and your content CI never touches a cloud service.

See [getting-started.md](getting-started.md) for the Tier 1 setup this builds on.
See [private-cloud-setup.md](private-cloud-setup.md) for Tier 2 (same stack on a rented VPS — no local hardware required).
For system architecture and component interfaces, see [second-brain-setup/architecture.md](../personal/projects/second-brain-setup/architecture.md).


## 🏗️ What Tier 3 adds

| | Tier 1 — Cloud | Tier 3 — Self-hosted |
|---|---|---|
| Git host | GitHub | Gitea (own hardware) |
| AI inference | Anthropic API | LiteLLM + Ollama (own hardware) |
| Semantic search | — | Qdrant + embedding model (own hardware) |
| Framework CI | GitHub Actions | GitHub Actions |
| Content CI | — | Gitea Actions |
| Hardware required | None | Own hardware + GPU (recommended) |
| Data sovereignty | Partial | Full |

Both tiers use Claude Code — the only difference is `ANTHROPIC_BASE_URL`. Tier 3 adds infrastructure alongside Tier 1; nothing is removed. GitHub Actions continues to run framework tests on your public fork; Gitea Actions handles content-aware automation (index generation, budget tests) that must not run on GitHub.


## 📋 Prerequisites

- Tier 1 setup complete — vault cloned, Claude Code working
- Docker and Docker Compose installed
- A machine to host Gitea and Ollama — always-on is recommended (home server, NAS, or VPS) but a local machine works for evaluation


## 🐳 Docker Compose

The canonical compose file is at [`_infrastructure/docker-compose.yml`](../_infrastructure/docker-compose.yml) in the framework. Copy the `_infrastructure/` folder to a convenient location outside your vault (e.g., `~/_infrastructure/`):

```bash
cp _infrastructure/docker-compose.yml _infrastructure/.env.example ~/_infrastructure/
cd ~/infra && cp .env.example .env
```

Services included:

| Service | Image | Purpose |
|---|---|---|
| `gitea` | `gitea/gitea` | Private git host for your vault |
| `ollama` | `ollama/ollama` | LLM and embedding model runtime (GPU enabled by default) |
| `litellm` | `ghcr.io/berriai/litellm` | Anthropic-compatible API gateway |
| `qdrant` | `qdrant/qdrant` | Vector store for semantic search |
| `gitea-runner` | `gitea/act_runner` | Gitea Actions CI runner |

Edit `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...        # from console.anthropic.com
LITELLM_KEY=sk-your-key-here        # LiteLLM master key — set to any strong secret
RUNNER_TOKEN=                        # fill in after Gitea is configured — see Gitea Actions section
```

Start Gitea and Ollama first (LiteLLM depends on Ollama being ready):

```bash
docker compose up -d gitea ollama
```

Verify:
- Gitea: `http://localhost:3000`
- Ollama: `http://localhost:11434` (returns `{"message":"Ollama is running"}`)

> If hosting on a home server, replace `localhost` with your machine's IP or domain throughout.


## ⚙️ Set up Gitea

### Initial configuration

1. Open `http://localhost:3000` — Gitea's first-run setup appears
2. Set database to **SQLite** (simplest for a personal setup)
3. Set your site URL (`http://localhost:3000` or your domain)
4. Create an admin account

### Create your repo

1. Create a new repository named `second-brain` (or your preferred name)
2. Leave it empty — you will push your existing vault to it

### SSH key

Add your public key to Gitea under **Settings → SSH / GPG Keys**. Generate one if needed:

```bash
ssh-keygen -t ed25519 -C "your-email"
cat ~/.ssh/id_ed25519.pub
```

Test the connection (Gitea SSH is on port 2222):

```bash
ssh -p 2222 -T git@localhost
```


## ⚡ Gitea Actions

Gitea Actions uses the same workflow syntax as GitHub Actions. The workflows in [`.gitea/workflows/`](../.gitea/workflows/) are already configured and run automatically once a runner is active.

### What Gitea Actions handles

| Workflow | Trigger | What it does |
|---|---|---|
| [`generate-artifacts.yml`](../.gitea/workflows/generate-artifacts.yml) | Push to `main` | Regenerates `_conversations/index.md`, project indexes, and `_conversations/pending-events.md` |

These workflows read your note content directly — that is why they run on Gitea, not GitHub. GitHub Actions runs only on the public framework fork, which never has access to your content. See [second-brain-setup/architecture.md — A2](../personal/projects/second-brain-setup/architecture.md#a2--gitea-actions-workflows) for the CI design rationale.

### Register the runner

1. Go to **Site Administration → Actions → Runners** in the Gitea web UI
2. Click **Create new runner** and copy the registration token
3. Set the token in a `.env` file next to your `docker-compose.yml`:

```bash
RUNNER_TOKEN=your-token-here
```

4. Start the runner:

```bash
docker compose up -d gitea-runner
```

Verify it appears as **Online** in **Site Administration → Actions → Runners**.


## 🔀 Migrate your vault to Gitea

Your vault currently has GitHub as `origin`. Reassign `origin` to Gitea and keep GitHub as `upstream` for framework sync:

```bash
git remote set-url origin ssh://git@localhost:2222/your-username/second-brain.git
git remote add upstream https://github.com/jctots/second-brain.git
git push -u origin main
```

Verify:

```bash
git remote -v
# origin    ssh://git@localhost:2222/your-username/second-brain.git
# upstream  https://github.com/jctots/second-brain.git
```


## 🦙 Pull a model

Pull a model into the running Ollama container:

```bash
docker exec -it ollama ollama pull qwen2.5:7b
```

For better reasoning quality if your hardware supports it:

```bash
docker exec -it ollama ollama pull qwen2.5:32b
```

Then start LiteLLM:

```bash
docker compose up -d litellm
```

Verify LiteLLM is running: `curl http://localhost:4000/health` should return OK.


## 🔍 Semantic search (RAG)

Tier 3 adds semantic search across your vault — notes surface by meaning, not just keyword. Two modes:

- **Active query:** run `/search "topic"` in a Claude Code session — returns ranked notes
- **Passive surfacing:** a hook automatically injects relevant notes into context at the start of each turn

Both require Qdrant (already in the Docker Compose above) and an embedding model in Ollama.

### Pull an embedding model

```bash
docker exec -it ollama ollama pull nomic-embed-text
```

`nomic-embed-text` is a good default — 768-dimension vectors, runs well on GPU or CPU. If your hardware supports it, `mxbai-embed-large` gives higher quality. The embedding model runs alongside your inference model — both serve requests from the same Ollama container.

### Index your vault

Run the indexer once manually to seed Qdrant:

```bash
python _scripts/embed-vault.py
```

This walks all vault `.md` files, chunks them by heading section, embeds each chunk, and upserts into Qdrant with metadata (file path, PARA category, context, project, tags from frontmatter). A full index of a typical vault takes a few minutes.

Set these environment variables before running (or add to your shell profile):

```bash
export QDRANT_URL=http://localhost:6333
export OLLAMA_EMBED_MODEL=nomic-embed-text   # match what you pulled above
export OLLAMA_URL=http://localhost:11434
```

### Automatic indexing on push

The Gitea Actions workflow `.gitea/workflows/embed-vault.yml` runs `embed-vault.py` automatically when `.md` files change on push — incrementally, only re-indexing changed files. No manual re-indexing needed after the first run.

For the runner to reach Qdrant, add the env vars as Gitea Actions secrets (**Site Administration → Actions → Secrets**):

| Secret | Value |
|---|---|
| `QDRANT_URL` | `http://qdrant:6333` (internal Docker network) |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` |
| `OLLAMA_URL` | `http://ollama:11434` (internal Docker network) |

### Enable passive surfacing

Register the RAG hook in `.claude/settings.json` alongside the existing context injection hooks:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      ...existing hooks...,
      {
        "matcher": "",
        "hooks": [{
          "type": "command",
          "command": "python _scripts/inject-context-rag.py"
        }]
      }
    ]
  }
}
```

The hook embeds each incoming message, queries Qdrant for the top matching notes (similarity threshold: 0.75), and injects the results as context before Claude sees your message. It degrades gracefully — if Qdrant is unreachable, it outputs nothing and the session continues normally.

### Verify

```bash
# search manually
python _scripts/search-vault.py "home lab infrastructure"
# expected: ranked list of file paths + headings + snippets

# or from inside a Claude Code session
/search "home lab infrastructure"
```

Then start a session on a topic you have notes on — relevant notes should appear in Claude's context without asking.


## ⚙️ Configure Claude Code

> **Requires Anthropic API key.** `ANTHROPIC_BASE_URL` only works with `ANTHROPIC_API_KEY` auth (from [console.anthropic.com](https://console.anthropic.com)). Incompatible with claude.ai subscription (OAuth). See [second-brain-setup/architecture.md — LiteLLM gateway interface](../personal/projects/second-brain-setup/architecture.md#litellm-gateway-interface) for the full gateway design.

Set these in your shell profile (`.bashrc`, `.zshrc`, or PowerShell profile):

```bash
export ANTHROPIC_API_KEY=sk-ant-...             # Anthropic Console API key
export ANTHROPIC_BASE_URL=http://localhost:4000  # LiteLLM endpoint
export ANTHROPIC_AUTH_TOKEN=sk-your-key-here     # LiteLLM key
```

Restart VS Code. Claude Code routes all inference through LiteLLM → Ollama — nothing reaches Anthropic's API directly.

**Switch models** using the `--model` flag — LiteLLM routes by model name per [`_infrastructure/litellm_config.yaml`](../_infrastructure/litellm_config.yaml):

```bash
claude --model claude-sonnet-4-6   # Anthropic via LiteLLM
claude --model llama3              # local Ollama
```

To return to Anthropic directly: comment out `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` (keep `ANTHROPIC_API_KEY`) and restart VS Code.


## 📱 Configure obsidian-git → Gitea

In the obsidian-git plugin settings:

1. Set **Remote URL** to `ssh://git@localhost:2222/your-username/second-brain.git`
2. Set **SSH key path** to your private key (e.g., `~/.ssh/id_ed25519`)

obsidian-git supports any git host over SSH — Gitea, Forgejo, and others all work the same way. See the [getting-started.md](getting-started.md) Obsidian section for the full mobile walkthrough.


## ✅ Verify the full setup

**Gitea Actions:**

```bash
echo "test" >> _inbox/test.md
git add _inbox/test.md && git commit -m "test: verify gitea actions"
git push origin main
```

Open **Actions** in the Gitea web UI — the workflow should appear and complete. Delete `_inbox/test.md` afterwards.

**Claude Code + LiteLLM:**

Open a Claude Code session. The hook announcement at session start confirms context injection is working. Check that `ANTHROPIC_BASE_URL` is set and that requests are routing through LiteLLM — nothing should reach Anthropic's API.
