# ☁️ Private Cloud Setup (Tier 2)

How to add a private cloud AI path to your second brain. Tier 2 gives you inference on user-controlled infrastructure without requiring local hardware — your LLM runs on a VPS you own, not on Anthropic's servers and not on your laptop.

See [getting-started.md](getting-started.md) for the Tier 1 setup this builds on.
See [self-hosted-setup.md](self-hosted-setup.md) for Tier 3 (same stack on your own hardware).
For system architecture and component interfaces, see [architecture.md](../personal/projects/second-brain-setup/architecture.md).


## 🏗️ What Tier 2 adds

| | Tier 1 — Cloud | Tier 2 — Private cloud |
|---|---|---|
| Git host | GitHub | Gitea on VPS |
| AI inference | Anthropic API | LiteLLM + Ollama on VPS |
| Semantic search | Keyword only | Qdrant + embedding model (VPS) |
| Framework CI | GitHub Actions | GitHub Actions |
| Content CI | — | Gitea Actions |
| Hardware required | None | VPS (GPU recommended) |
| Data sovereignty | Partial | Inference on user-controlled infra |

Both tiers use Claude Code — the only difference is `ANTHROPIC_BASE_URL`. Unset it to return to the Anthropic API at any time. Hooks, slash commands, and conversation saving work identically.


## 📋 Prerequisites

- Tier 1 setup complete — vault cloned, Claude Code working
- A VPS — Hetzner CX32 (4 vCPU, 8GB RAM, ~€8/mo) is the recommended minimum for CPU-only 7B inference. DigitalOcean and Linode are viable alternatives at higher cost for equivalent specs.
- Docker and Docker Compose on the VPS
- A domain or subdomain pointing at the VPS (recommended — Caddy handles HTTPS automatically)


## 🐳 Docker Compose

The canonical compose file is at [`_infrastructure/docker-compose.yml`](../_infrastructure/docker-compose.yml) in the framework. Copy the `_infrastructure/` folder to a convenient location on your VPS (e.g., `~/_infrastructure/`) and add Caddy via the `https` profile:

```bash
scp _infrastructure/docker-compose.yml _infrastructure/.env.example _infrastructure/Caddyfile.example user@your-vps:~/_infrastructure/
ssh user@your-vps "cd ~/infra && cp .env.example .env && cp Caddyfile.example Caddyfile"
```

Services included:

| Service | Image | Purpose |
|---|---|---|
| `ollama` | `ollama/ollama` | LLM and embedding model runtime |
| `litellm` | `ghcr.io/berriai/litellm` | Anthropic-compatible API gateway |
| `qdrant` | `qdrant/qdrant` | Vector store for semantic search |
| `caddy` | `caddy` | HTTPS reverse proxy |

Ollama, LiteLLM, and Qdrant bind to `127.0.0.1` — Caddy is the only externally reachable service.

Edit `.env` on the VPS:

```bash
ANTHROPIC_API_KEY=sk-ant-...        # from console.anthropic.com
LITELLM_KEY=sk-your-key-here        # LiteLLM master key — set to any strong secret
RUNNER_TOKEN=                        # fill in after Gitea is configured
```


## 🔒 Caddy configuration

Create a `Caddyfile` next to `docker-compose.yml`:

```
ai.yourdomain.com {
    reverse_proxy litellm:4000
}
```

Caddy handles TLS certificate provisioning automatically. Replace `ai.yourdomain.com` with your subdomain.

Start everything including Caddy:

```bash
docker compose --profile https up -d
```

Verify Caddy is serving HTTPS: `curl https://ai.yourdomain.com` should return a LiteLLM response.


## 🦙 Pull a model

```bash
docker exec -it ollama ollama pull qwen2.5:7b
```

For CPU-only inference, 7B models are the practical ceiling for reasonable response times. Smaller models (`llama3.2:3b`) are faster but lower quality — start with 7B and adjust based on response latency on your hardware.


## ⚙️ Configure Claude Code

> **Requires Anthropic API key.** `ANTHROPIC_BASE_URL` only works with `ANTHROPIC_API_KEY` auth (from [console.anthropic.com](https://console.anthropic.com)). Incompatible with claude.ai subscription (OAuth). See [architecture.md — LiteLLM gateway interface](../personal/projects/second-brain-setup/architecture.md#litellm-gateway-interface) for the full gateway design.

Set these in your shell profile (`.bashrc`, `.zshrc`, or PowerShell profile):

```bash
export ANTHROPIC_API_KEY=sk-ant-...                    # Anthropic Console API key
export ANTHROPIC_BASE_URL=https://ai.yourdomain.com    # LiteLLM endpoint
export ANTHROPIC_AUTH_TOKEN=sk-your-key-here           # LiteLLM key
```

Restart VS Code. Claude Code routes all inference through your VPS — nothing reaches Anthropic's API directly.

**Switch models** using the `--model` flag — LiteLLM routes by model name per [`_infrastructure/litellm_config.yaml`](../_infrastructure/litellm_config.yaml):

```bash
claude --model claude-sonnet-4-6   # Anthropic via LiteLLM
claude --model llama3              # Ollama on your VPS
```

To return to Anthropic directly: comment out `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` (keep `ANTHROPIC_API_KEY`) and restart VS Code.


## 🔍 Semantic search (RAG)

Tier 2 adds semantic search across your vault. The setup mirrors Tier 3 with one key difference: no GPU. The VPS runs CPU-only inference, so choose a lightweight embedding model.

Two modes:

- **Active query:** run `/search "topic"` in a Claude Code session
- **Passive surfacing:** a hook automatically injects relevant notes into context at the start of each turn

### Pull an embedding model

```bash
docker exec -it ollama ollama pull nomic-embed-text
```

`nomic-embed-text` (768-dimension vectors) is a good default. If your VPS has a GPU, `mxbai-embed-large` gives higher quality. Without a GPU, `all-minilm` (384 dims) is faster at the cost of some accuracy — test with your hardware.

### Index your vault

Run the indexer once manually from your local machine, pointed at the VPS:

```bash
export QDRANT_URL=https://qdrant.yourdomain.com   # or http://your-vps-ip:6333 if not proxied
export OLLAMA_EMBED_MODEL=all-minilm
export OLLAMA_URL=https://ai.yourdomain.com        # your LiteLLM/Ollama endpoint
python _scripts/embed-vault.py
```

Or SSH into the VPS and run it there with internal Docker network addresses (`http://qdrant:6333`, `http://ollama:11434`).

### Automatic indexing on push

The Gitea Actions workflow `.gitea/workflows/embed-vault.yml` handles incremental re-indexing on every push that changes `.md` files. Add the env vars as Gitea Actions secrets (**Site Administration → Actions → Secrets**):

| Secret | Value |
|---|---|
| `QDRANT_URL` | `http://qdrant:6333` (internal Docker network) |
| `OLLAMA_EMBED_MODEL` | `all-minilm` |
| `OLLAMA_URL` | `http://ollama:11434` (internal Docker network) |

### Enable passive surfacing

Register the RAG hook in `.claude/settings.json` (same as Tier 3):

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

The hook queries your VPS Qdrant instance via `QDRANT_URL`. Degrades gracefully if the VPS is unreachable.

### Verify

```bash
python _scripts/search-vault.py "topic"
# or inside a Claude Code session:
/search "topic"
```

> **Embedding model consistency:** the model used to index and to query must match. If you change models, re-run `embed-vault.py` in full (not incremental) to rebuild the Qdrant collection.


## ⚡ Gitea and Gitea Actions

Tier 2 uses the same Gitea setup as Tier 3 — content hosted on your own infrastructure, Gitea Actions for content-aware CI (index generation, budget tests) that must not run on GitHub. See [self-hosted-setup.md](self-hosted-setup.md) for the full Gitea setup — the steps are identical whether Gitea runs on a VPS or local hardware.

| Workflow | Trigger | What it does |
|---|---|---|
| [`generate-artifacts.yml`](../.gitea/workflows/generate-artifacts.yml) | Push to `main` | Regenerates `_conversations/index.md`, project indexes, and `_conversations/pending-events.md` |


## ✅ Verify

**Gitea Actions:**

```bash
echo "test" >> _inbox/test.md
git add _inbox/test.md && git commit -m "test: verify gitea actions"
git push origin main
```

Open **Actions** in the Gitea web UI — the workflow should appear and complete. Delete `_inbox/test.md` afterwards.

**Claude Code + LiteLLM:**

```bash
curl -X POST https://ai.yourdomain.com/v1/messages \
  -H "Authorization: Bearer sk-your-key-here" \
  -H "Content-Type: application/json" \
  -d '{"model": "ollama/qwen2.5:7b", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}'
```

Then open a Claude Code session — the hook announcement at session start confirms context injection is working normally.


## ⚠️ Feature degradation

Some Claude Code features require Anthropic-specific model capabilities:

| Feature | Anthropic API | Local model via LiteLLM |
|---|---|---|
| Agentic tool use (multi-step) | Full | Degraded — model quality dependent |
| Extended thinking / effort levels | Available | Not available |
| Prompt caching | Available | Not available |
| Hooks + slash commands | Available | Available — unaffected |
| Conversation saving | Available | Available — unaffected |

Use Tier 2 for sensitive-content queries and routine tasks. Complex agentic work benefits from the Anthropic API (Tier 1).
