# 🔒 Privacy

This document explains what data leaves your machine when using this system, what stays local, and how to control your exposure.


## 🏠 Your vault is yours

Notes are plain Markdown files stored on your machine and in your own git repository. There is no background sync, no cloud storage, no third-party indexing of your vault.

Whether notes leave your machine during AI sessions depends on the inference tier you use — see below.


## 🤖 Three inference paths — choose your boundary

Claude Code is the AI interface at every deployment tier. What changes is where inference happens:

| Tier | Inference | Data sent to Anthropic? |
|---|---|---|
| 1 — Cloud | Anthropic API | Yes — session context sent to Anthropic's servers |
| 2 — Private cloud | LiteLLM + Ollama (VPS) | No — inference stays on your VPS |
| 3 — Self-hosted | LiteLLM + Ollama (own hardware) | No — inference stays on your hardware |

**Tier 1** is the default out-of-the-box experience. It is the right choice for non-sensitive content and framework evaluation. If your second brain contains personal, health, financial, or professional content, consider Tier 2 or Tier 3.

**Tier 2 and 3** route inference through a LiteLLM gateway to a local Ollama model. Nothing reaches Anthropic's API. See [docs/private-cloud-setup.md](docs/private-cloud-setup.md) (Tier 2) and [docs/self-hosted-setup.md](docs/self-hosted-setup.md) (Tier 3).


## ⚠️ Tier 1 privacy caveat

At Tier 1, every session sends data to Anthropic's API — your profile summary, active project context, and everything you type or share during the session. The full vault is never sent automatically; only what Claude Code reads and the messages you write.

**Anthropic's data policy:** API inputs and outputs are not used to train models by default. This applies to Claude Code sessions. Full policy: [anthropic.com/privacy](https://www.anthropic.com/privacy).


## ☁️ Tier 2 privacy caveat

Tier 2 routes inference through a VPS you rent — not hardware you own. This shifts the trust boundary from Anthropic to your infrastructure provider (Hetzner, DigitalOcean, Linode, etc.).

What this means in practice:

- Your VPS provider has physical access to the hardware and could in principle access disk and memory
- Session context travels over the internet to reach the VPS — HTTPS (Caddy) encrypts the transport, but the VPS sees plaintext during inference
- You are trusting rented infrastructure, not owned infrastructure

**Tier 2's privacy claim:** no AI company sees your data. Not: no one sees your data.

If your content requires the strongest privacy guarantee — personal health records, legal documents, sensitive financial data — use Tier 3. Tier 3 is the only path where nothing leaves hardware you physically control.


## 🏠 Tier 3 privacy caveat

Tier 3 gives you the strongest data boundary — no AI company, no VPS provider, no internet path for session content. But full control comes with full responsibility.

Residual concerns:

- **Model download** — `ollama pull` fetches weights from Ollama's servers. Your IP and model name are visible to Ollama's CDN once per model pull, not per session.
- **Network exposure** — Ollama and LiteLLM may bind to `0.0.0.0` by default, making them reachable by other devices on your local network. Firewall them if you're on a shared or untrusted network.
- **Physical security** — the hardware is in your home or office. Physical access to the machine means access to the data and the model's inference history.

**The real disclaimer:** at Tier 3, you are the security boundary. There is no provider SLA, no managed firewall, no intrusion detection — only what you configure yourself. You need to judge honestly whether you trust your own ability to secure a home server: network segmentation, OS patching, physical access controls, and detecting anomalous behaviour.

If that sounds like more than you want to manage, Tier 2 is the better tradeoff — you pay a VPS provider to handle infrastructure security while still keeping your data away from AI companies. The privacy guarantee is slightly weaker, but the operational burden is much lower.
