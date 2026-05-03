# 🏠 Self-Hosted Setup (Tier 2)

How to add Gitea and Ollama alongside your existing GitHub + Claude Code setup. Tier 2 gives you full data sovereignty — your notes are hosted privately, your LLM runs locally, and your content CI never touches a cloud service.

See [getting-started.md](getting-started.md) for the Tier 1 setup this builds on.


## 🏗️ What Tier 2 adds

| | Tier 1 — Evaluation | Tier 2 — Full private |
|---|---|---|
| Git host | GitHub | Gitea (self-hosted) |
| AI | Claude Code | Continue.dev + Ollama |
| Framework CI | GitHub Actions | GitHub Actions |
| Content CI | — | Gitea Actions |
| Data sovereignty | Partial | Full |

Both tiers use the same framework from the upstream GitHub repo. Tier 2 adds infrastructure alongside — nothing from Tier 1 is removed. GitHub Actions continues to run framework tests on your public fork; Gitea Actions handles content-aware automation (index generation, budget tests) that must not run on GitHub.


## 📋 Prerequisites

- Tier 1 setup complete — vault cloned, Claude Code working
- Docker and Docker Compose installed
- A machine to host Gitea and Ollama — always-on is recommended (home server, NAS, or VPS) but a local machine works for evaluation


## 🐳 Docker Compose

Create a `docker-compose.yml` in a convenient location outside your vault (e.g., `~/infra/`):

```yaml
services:
  gitea:
    image: gitea/gitea:latest
    container_name: gitea
    environment:
      - USER_UID=1000
      - USER_GID=1000
    restart: unless-stopped
    ports:
      - "3000:3000"
      - "2222:22"
    volumes:
      - gitea-data:/data

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama

  gitea-runner:
    image: gitea/act_runner:latest
    container_name: gitea-runner
    restart: unless-stopped
    environment:
      - GITEA_INSTANCE_URL=http://gitea:3000
      - GITEA_RUNNER_REGISTRATION_TOKEN=${RUNNER_TOKEN}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - gitea

volumes:
  gitea-data:
  ollama-data:
```

The runner token is set after Gitea is configured — see the Gitea Actions section below.

Start Gitea and Ollama first:

```bash
docker compose up -d gitea ollama
```

Verify:
- Gitea: `http://localhost:3000`
- Ollama: `http://localhost:11434` (returns `{"message":"Ollama is running"}`)

> If hosting on a home server or VPS, replace `localhost` with your machine's IP or domain throughout.


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

Gitea Actions uses the same workflow syntax as GitHub Actions. The workflows in `.gitea/workflows/` are already configured and run automatically once a runner is active.

### What Gitea Actions handles

| Workflow | Trigger | What it does |
|---|---|---|
| `index-conversations.yml` | Push to `main` when `_conversations/` changes | Regenerates `_conversations/index.md` |

These workflows read your note content directly — that is why they run on Gitea, not GitHub. GitHub Actions runs only on the public framework fork, which never has access to your content.

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

Then configure Continue.dev to point at `http://localhost:11434`. See [continue-integration.md](continue-integration.md) for the full configuration and model recommendations.


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

**Continue.dev + Ollama:**

Open a Continue.dev session and run `/load-context second-brain-setup`. Confirm the session loads context and all requests stay local — nothing sent to any external API.
