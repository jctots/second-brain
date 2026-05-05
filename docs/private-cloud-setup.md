# ☁️ Private Cloud Setup (Tier 2)

How to add a private cloud AI path to your second brain. Tier 2 gives you inference on user-controlled infrastructure without requiring local hardware — your LLM runs on a VPS you own, not on Anthropic's servers and not on your laptop.

See [getting-started.md](getting-started.md) for the Tier 1 setup this builds on.
See [self-hosted-setup.md](self-hosted-setup.md) for Tier 3 (same stack on your own hardware).


## 🏗️ What Tier 2 adds

| | Tier 1 — Cloud | Tier 2 — Private cloud |
|---|---|---|
| Git host | GitHub | Gitea on VPS |
| AI inference | Anthropic API | LiteLLM + Ollama on VPS |
| Framework CI | GitHub Actions | GitHub Actions |
| Content CI | — | Gitea Actions |
| Hardware required | None | None (VPS subscription) |
| Data sovereignty | Partial | Inference on user-controlled infra |

Both tiers use Claude Code — the only difference is `ANTHROPIC_BASE_URL`. Unset it to return to the Anthropic API at any time. Hooks, slash commands, and conversation saving work identically.


## 📋 Prerequisites

- Tier 1 setup complete — vault cloned, Claude Code working
- A VPS — Hetzner CX32 (4 vCPU, 8GB RAM, ~€8/mo) is the recommended minimum for CPU-only 7B inference. DigitalOcean and Linode are viable alternatives at higher cost for equivalent specs.
- Docker and Docker Compose on the VPS
- A domain or subdomain pointing at the VPS (recommended — Caddy handles HTTPS automatically)


## 🐳 Docker Compose

Create a `docker-compose.yml` on the VPS (e.g., in `~/infra/`):

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "127.0.0.1:11434:11434"
    volumes:
      - ollama-data:/root/.ollama

  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: litellm
    restart: unless-stopped
    ports:
      - "127.0.0.1:4000:4000"
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_KEY}
    command: --model ollama/qwen2.5:7b --port 4000
    depends_on:
      - ollama

  caddy:
    image: caddy:latest
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy-data:/data

volumes:
  ollama-data:
  caddy-data:
```

Set your LiteLLM key in a `.env` file next to `docker-compose.yml`:

```bash
LITELLM_KEY=sk-your-key-here
```

Ollama and LiteLLM bind to `127.0.0.1` only — Caddy is the only externally reachable service.


## 🔒 Caddy configuration

Create a `Caddyfile` next to `docker-compose.yml`:

```
ai.yourdomain.com {
    reverse_proxy litellm:4000
}
```

Caddy handles TLS certificate provisioning automatically. Replace `ai.yourdomain.com` with your subdomain.

Start everything:

```bash
docker compose up -d
```

Verify Caddy is serving HTTPS: `curl https://ai.yourdomain.com` should return a LiteLLM response.


## 🦙 Pull a model

```bash
docker exec -it ollama ollama pull qwen2.5:7b
```

For CPU-only inference, 7B models are the practical ceiling for reasonable response times. Smaller models (`llama3.2:3b`) are faster but lower quality — start with 7B and adjust based on response latency on your hardware.


## ⚙️ Configure Claude Code

Set these in your shell profile (`.bashrc`, `.zshrc`, or PowerShell profile):

```bash
export ANTHROPIC_BASE_URL=https://ai.yourdomain.com
export ANTHROPIC_AUTH_TOKEN=sk-your-key-here
```

Restart VS Code. Claude Code routes all inference through your VPS — nothing reaches Anthropic's API.

To return to Anthropic: comment out both variables and restart VS Code.


## ⚡ Gitea and Gitea Actions

Tier 2 uses the same Gitea setup as Tier 3 — content hosted on your own infrastructure, Gitea Actions for content-aware CI (index generation, budget tests) that must not run on GitHub. See [self-hosted-setup.md](self-hosted-setup.md) for the full Gitea setup — the steps are identical whether Gitea runs on a VPS or local hardware.


## ✅ Verify

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
