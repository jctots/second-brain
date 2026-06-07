# Configuration

Reference for `python _scripts/setup.py` options 2 and 3.

```
1. Full setup — pip deps, VS Code extensions, optional services
2. Optional services only
3. Change configuration
```


## Option 2 — Optional services

Configures credentials and connection details for optional services. All values are written to `.env` at vault root (gitignored) unless noted otherwise. Run `setup.py` and select the service number(s) to configure, or enter `all` to configure everything not yet set, or `r` to reconfigure an existing service.

### RAG (Ollama + Qdrant)

Passive note surfacing (every session, no action needed) and active search via `/search`. Tier 2/3 only.

| Variable | Notes |
|---|---|
| `OLLAMA_HOST` | Ollama hostname or IP — RAG is disabled if empty |
| `OLLAMA_PORT` | Default: `11434` |
| `QDRANT_HOST` | Qdrant hostname or IP — RAG is disabled if empty |
| `QDRANT_PORT` | Default: `6333` |

After configuring: trigger the first embed run via CI (`rag-embed-vault.yml` → Run workflow) or run `python _scripts/rag-embed.py` locally.

RAG tuning variables (edit `.env` directly):

| Variable | Default | Notes |
|---|---|---|
| `RAG_COLLECTION` | `second_brain` | Qdrant collection name |
| `RAG_EMBED_MODEL` | `embeddinggemma:latest` | Ollama model used for embedding |
| `RAG_QUERY_LIMIT` | `10` | Raw results fetched before filtering |
| `RAG_MAX_FILES` | `3` | Max note titles injected per turn |
| `RAG_SCORE_THRESHOLD` | `0.30` | Minimum similarity score |
| `RAG_TIMEOUT` | `5` | Request timeout in seconds |

### ntfy

Push notifications for session events and CI failures.

| Variable | Default | Notes |
|---|---|---|
| `NTFY_URL` | (none) | ntfy server base URL — notifications disabled if empty |
| `NTFY_TOPIC` | `second-brain` | Topic name used for all notifications |
| `NTFY_ON_EVENTS` | `true` | Notify on unprocessed session events |

For CI failure notifications: add `NTFY_URL` and `NTFY_TOPIC` as Gitea secrets (Settings → Secrets). CI reads from Gitea secrets, not `.env`.

Toggle `NTFY_ON_EVENTS` via setup.py option 3 → ntfy events, or edit `.env` directly.

Service health failures are reported in-conversation (via `check-health.py` UserPromptSubmit hook), not via ntfy.

### Vikunja

Task sync — `/remember` writes next actions to a Vikunja project; `/maintain` closes completed tasks.

| Variable | Notes |
|---|---|
| `VIKUNJA_URL` | Base URL, no `/api/v1` suffix |
| `VIKUNJA_TOKEN` | API token — Vikunja: Settings → API Tokens → create with unlimited scope |

`setup.py` also creates `.mcp.json` at vault root (gitignored) and installs `vikunja-mcp` via pip. Restart Claude Code after configuring for MCP to take effect.

### Gitea

Service health check — `check-health.py` verifies Gitea is reachable at session start.

| Variable | Notes |
|---|---|
| `GITEA_URL` | Base URL of your Gitea instance (e.g. `https://git.example.com`) |
| `GITEA_TOKEN` | Personal access token — Gitea: Settings → Applications → Generate token |

Add both to `.env` manually. If either is absent, the Gitea check is skipped.

### LiteLLM

Routes Claude Code to a private Ollama instance. Tier 2/3 only. Cannot be auto-configured — set these in your shell profile (`.bashrc` / `.zshrc` / PowerShell profile):

```
ANTHROPIC_BASE_URL=http://<litellm-host>:4000
ANTHROPIC_AUTH_TOKEN=<your-litellm-key>
```

Unset both to return to the Anthropic API. See [private-cloud-setup.md](private-cloud-setup.md) or [self-hosted-setup.md](self-hosted-setup.md) for full setup.


## Option 3 — Change configuration

### 3.1 PDF sidecars

PDF sidecars are controlled via a Gitea Actions variable — not in `.env`. The CI step installs `tesseract`, `pdfplumber`, and `pypdfium2` automatically when enabled.

**To enable:** Gitea → your repo → Settings → Variables → Add variable
- Name: `PDF_SIDECARS_ENABLED`
- Value: `true`

**To disable:** delete the variable or set it to any value other than `true`.

### 3.2 Hook budget

Controls when files in `_self/` and project `CLAUDE.md`/`_memory.md` trigger warnings. Edit `.env` directly:

| Variable | Default | Notes |
|---|---|---|
| `HOOK_BUDGET_HARD` | `10000` | Hard char limit per file — CI fails above this |
| `HOOK_BUDGET_WARN_PCT` | `80` | Warn threshold as % of the hard limit |

Affects: `test_hook_budget.py` (CI), `generate-dashboard.py` (budget section in dashboard).

### 3.3 ntfy events

Toggle which local notification points are active. Run `setup.py` → option 3 → ntfy events, or edit `.env` directly:

| Variable | Default | Effect when `false` |
|---|---|---|
| `NTFY_ON_EVENTS` | `true` | Session-end notifications silenced |

Setting to `false` does not affect CI notifications — those are controlled by whether Gitea secrets `NTFY_URL` and `NTFY_TOPIC` are set.

Service health failures are always shown in-conversation (first turn of each session) regardless of this setting.

### 3.4 Git remotes

Run `setup.py` → option 3 → git remotes to update `origin` and `upstream` interactively. Current URLs are shown before prompting. Press Enter to keep a value unchanged.

| Remote | Purpose |
|---|---|
| `origin` | Your private git host (Gitea for Tier 2/3, GitHub fork for Tier 1) |
| `upstream` | Public GitHub framework repo — used by `/sync` and `/contribute` |

Tier 1 users: `upstream` is optional. Skip it if your GitHub fork IS your origin.
