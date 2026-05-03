---
context: personal
para: projects
created: 2026-04-24
---

# Second Brain — Decisions

[[second-brain-setup/index|⬅️ Project Index]]

> Design history — choices between real alternatives, with rationale. Newest first.
> Add an entry whenever a non-obvious choice is made. Link back to the requirement that motivated it.

---

## D20 — 2026-05-03 — `.gitignore merge=ours` flows to all downstream forks

**Decision:** Added `.gitignore merge=ours` to the upstream repository's `.gitattributes`. Since `.gitattributes` flows downstream on first merge, all forks automatically inherit `.gitignore` protection before they need it.
**Why:** The upstream `.gitignore` blocks content paths. Downstream instances need their own `.gitignore` that allows content commits to private infrastructure. Without this rule, `git merge upstream/main` would silently overwrite the instance's `.gitignore`. Shipping the rule in `.gitattributes` is the only way to guarantee it's in place before the first merge.
**Alternatives considered:** Document manual reconcile on merge — rejected; too error-prone. Require each instance to add `merge=ours` in setup docs — rejected; the rule must exist before the first upstream merge, and users might merge before reading setup docs.

---

## D19 — 2026-05-03 — `.gitignore` uses `dir/**` with explicit subdirectory negations

**Decision:** Content paths in the upstream `.gitignore` use `dir/**` (ignore contents, allow descent) rather than `dir/` (ignore directory entirely), with explicit `!dir/subdir/` negations for each PARA subdirectory and `.gitkeep` files.
**Why:** `dir/` tells git not to descend at all, making negation rules inside unreachable. `dir/**` ignores contents but preserves descent, so `!dir/subdir/` and `!dir/subdir/.gitkeep` negations work correctly. (R8)
**Alternatives considered:** `dir/` with top-level negation — rejected; git does not recurse into a fully ignored directory to apply negations regardless of how specific the negation pattern is.

---

## D18 — 2026-05-03 — Tier 1/Tier 2 deployment model documented in public setup guides

**Decision:** Named and documented two deployment tiers in `docs/getting-started.md`. Tier 1: GitHub fork + cloud AI. Tier 2: Gitea + Ollama + local AI. The README keeps prose framing; tier labels appear in setup docs where structure matters.
**Why:** The two-path framing needed a clear upgrade path story. Tier labels give readers a mental model for what they're adding and why, without forcing infrastructure decisions upfront. (R4)
**Alternatives considered:** Keep "cloud path"/"local-first path" language throughout — rejected; the tier framing adds clarity for the setup progression without implying a one-time choice.

---

## D17 — 2026-05-02 — Workspace-scoped AI memory retired; all memory lives in vault files

**Decision:** All persistent AI memory for this repo lives in vault files: `_self/about.md` (profile + behavioral patterns), `_self/rules.md` (feedback rules), and project `_memory.md` files. Workspace-scoped memory (`.claude/projects/.../memory/`) is not used.
**Why:** Workspace memory is machine-local and does not travel with the repo. Vault files are git-versioned, readable in Obsidian, and injected via hooks with independent budgets. Two parallel memory systems created split sources of truth. (R2, R3)
**Alternatives considered:** Keep workspace memory for behavioral feedback only — rejected; portability and Obsidian-visibility advantages of vault files outweigh the convenience of the harness-native system.

---

## D16 — 2026-04-30 — Continue.dev + Ollama chosen as Tier 2 AI tool; slash command parity as design goal

**Decision:** Continue.dev is the local-first AI path alongside Claude Code. Every Claude Code slash command (`.claude/commands/`) has a Continue.dev equivalent (`.continue/prompts/`). Slash command parity is the primary reason Continue.dev was chosen over Cline.
**Why:** A second brain captures sensitive content — the local-first path must not degrade the workflow relative to the cloud path. Cline has no native slash command equivalent; workflows would degrade to conversational prompts. Continue.dev's slash command support enables identical command invocation across both paths. (R4)
**Alternatives considered:** Cline — rejected; no native slash command equivalent. Single-path setup — rejected; forces privacy compromise on one class of content.
**Tradeoffs accepted:** Continue.dev has no hooks equivalent — context loading is manual (prompt templates), not auto-injected. System changes must account for both paths.

---

## D15 — 2026-04-29 — Your instance is a downstream fork; all contributions go through branch → PR

**Decision:** The upstream repository (public GitHub) is the active upstream for all instances, including the repository owner's instance. Every instance uses `git fetch upstream && git merge` to pull improvements. All contributions go through branch → PR, with no direct pushes to main for any contributor.
**Why:** Making the owner's instance structurally identical to any community fork means the owner validates the contribution workflow by using it themselves. Any friction they encounter is assumed to affect all contributors. (R9)
**Alternatives considered:** Owner pushes directly to upstream main — rejected; breaks contributor workflow parity and removes the owner's ability to experience the fork workflow as community members do.

---

## D14 — 2026-04-29 — CI split: `.gitea/workflows/` for private CI; `.github/workflows/` for framework tests only

**Decision:** `.gitea/workflows/` is a framework path included in the upstream as a reference template for Tier 2 self-hosted CI. `.github/workflows/` is also a framework path but scoped to framework tests only — not content-aware automation.
**Why:** Tier 2 instances on Gitea need `.gitea/workflows/` for private CI; it must be available in the upstream as the reference. GitHub Actions cannot run content-aware CI because content never reaches GitHub (R8). Separating the two makes the tier boundary explicit in the repo structure.
**Alternatives considered:** `.gitea/workflows/` as instance-only — rejected; Tier 2 instances need it and can't inherit it if it's not in the upstream. `.github/workflows/` covering all automation — rejected; content-triggered workflows would never fire on GitHub.

---

## D13 — 2026-04-29 — Gitea designated as Tier 2 system dependency for private CI

**Decision:** Self-hosted Gitea is a Tier 2 system dependency, the same way Ollama is a dependency for private AI. Private CI (conversation indexing, content-aware tests) requires a hosting platform where content can be pushed — GitHub is excluded by R8.
**Why:** Content-aware CI cannot run on GitHub Actions because content never reaches GitHub. The only path to automated private CI is a self-hosted platform. Gitea is already the content hosting layer for Tier 2 — adding CI there is a natural extension, not a new dependency. (R5, R8)
**Alternatives considered:** GitHub Actions for content CI — rejected; content never reaches GitHub. Accept no private CI — rejected; conversation indexing is a framework feature and should work for all full instances. Separate CI service — rejected; Gitea already runs on the same server and has built-in Actions support.

---

## D12 — 2026-04-29 — Two deployment tiers: Evaluation and Full private

**Decision:** Document two supported deployment tiers. Tier 1 (Evaluation): GitHub fork + cloud AI — lower setup bar, explicit privacy caveats. Tier 2 (Full private): GitHub + self-hosted Gitea + Ollama — maximum privacy, full feature set.
**Why:** A single "full setup" requirement would block adoption — requiring a home server on day one is too high a bar. Naming the tiers and documenting the privacy tradeoffs is more honest than implying GitHub-only is fully private. Gives a clear upgrade path rather than a binary choice. (R4)
**Alternatives considered:** Single setup path (Tier 2 only) — rejected; too high a barrier for evaluation and contribution. Undocumented tiers — rejected; users would assume GitHub-only is fully private.

---

## D11 — 2026-04-29 — Independent hook injection budgets per script

**Decision:** Four separate inject scripts run as independent `UserPromptSubmit` hook commands, each with its own ~10,000 character budget. A single combined script would share one budget across all four files.
**Why:** The cap is per hook command, not per event. Independent budgets let each file use up to 9,500 chars safely. The cap mechanism redirects output over the limit to a file reference — nearly useless for context injection — so staying under budget is essential. (R6)
**Alternatives considered:** Single combined inject script — rejected; shares one budget, forcing arbitrary splits; doesn't fix the root problem.

---

## D10 — 2026-04-29 — Automated tests in `_tests/` enforce requirements in CI

**Decision:** A `_tests/` folder at repo root holds Python test scripts that run in CI on every push, starting with `test_r6_hook_budget.py`. Tests target specific requirements. CI blocks on failure.
**Why:** Requirements were stated but unverified — prose criteria require manual evaluation on every change. Executable tests enforce requirements automatically and fail loudly. CI is the right host: controlled environment, always reproducible, no local dependencies. (R6)
**Alternatives considered:** Prose verification criteria per requirement — rejected; requires human evaluation on every change, doesn't catch regressions automatically. Tests in `_scripts/` — rejected; `_scripts/` is for vault utilities; separating by purpose keeps each folder's role clear.

---

## D9 — 2026-04-28 — Local LLM as privacy architecture, not just vendor portability

**Decision:** The Tier 2 local LLM path (Ollama) is framed as privacy architecture — data sovereignty for a comprehensive second brain — not just vendor hedge or cost control.
**Why:** A second brain is complete by design: sensitive personal, family, professional, and client content will always be present. Content discipline (filtering what you capture) contradicts the system's purpose. The only genuine privacy solution for comprehensive capture is local LLM processing. (R4)
**Alternatives considered:** Content discipline — rejected; contradicts the comprehensive-capture premise. Cloud-only with user discretion — rejected; places the privacy burden on the user for every note they capture.

---

## D8 — 2026-04-28 — Extended section pattern for project `_memory.md` files

**Decision:** Project `_memory.md` files may contain a `<!-- extended -->` marker. Inject scripts strip everything at and below the marker — only the summary section is injected and counts toward the budget. Extended content loads on demand by reading the file directly.
**Why:** Budget constraints forced lossy trimming of valuable detail. The delimiter pattern preserves information without inflating the injected payload. A single file avoids sync drift between two files representing the same content. (R6, A1)
**Alternatives considered:** Two separate files (summary + archive) — rejected; creates a sync problem between two representations of the same content. Injecting everything — not possible; Claude Code cap is fixed per hook command.

---

## D7 — 2026-04-27 — CI owns derived artifacts; local hooks only for commit-blocking validation

**Decision:** Index regeneration runs exclusively in CI on push. Local hooks do not run these scripts. Local hooks are reserved for operations that must block a bad commit.
**Why:** A local hook that modifies an index file creates merge conflicts when CI has already committed an updated version. Both index scripts are fully deterministic — CI is the right and only place to run them. (A2)
**Alternatives considered:** Keep local hooks, disable CI — rejected; CI is more reliable and reproducible. Run both — rejected; causes merge conflicts on push.

---

## D6 — 2026-04-26 — Scripts in `_scripts/`, Python stdlib, cross-platform

**Decision:** All hook and CI scripts live in `_scripts/` and are written in Python using stdlib only. No PowerShell-only or bash-only scripts in `_scripts/`.
**Why:** Scripts are triggered by both Claude Code hooks (Windows) and CI runners (Linux). Keeping them in `_scripts/` signals they're repo-level utilities, not tool-specific artifacts. Python + `pathlib` runs on Windows, Linux, and macOS without extra setup or hardcoded path separators. (R2)
**Alternatives considered:** Keep scripts in `.claude/` — rejected once dual-trigger use case was established. PowerShell scripts — rejected; not native on Linux CI runners.

---

## D5 — 2026-04-26 — `infra.yaml` as single source of truth for tooling requirements

**Decision:** `infra.yaml` at repo root declares all tooling requirements (Python version, VS Code extensions). Setup scripts read it. No other file declares infrastructure requirements.
**Why:** Without a single source, tooling requirements scatter across per-tool config files that must be kept in sync. A single file is easier to maintain and audit. (R3)
**Alternatives considered:** `.python-version` + `.vscode/extensions.json` — rejected; fragmentation requires two files for two dimensions of the same requirement.

---

## D4 — 2026-04-26 — Hook-backed context injection; CLAUDE.md instructions are not guaranteed

**Decision:** Context injection (`_self/about.md`, project `CLAUDE.md`, project `_memory.md`) is implemented as `UserPromptSubmit` hooks, not as CLAUDE.md instructions that tell Claude to read files.
**Why:** In practice, CLAUDE.md startup instructions get skipped when the first user message is a direct question. Hooks fire unconditionally — no Claude compliance required. If a behavior must happen every session, it needs a hook. (A3)
**Alternatives considered:** CLAUDE.md instruction to read files at session start — rejected once the pattern of failure was confirmed. Slash command to load context — rejected; requires user action and is easy to forget.

---

## D3 — 2026-04-25 — Wikilinks everywhere; shortest-unique-path format for cross-tool compatibility

**Decision:** All internal links use wikilink syntax (`[[filename]]` or `[[filename|label]]`). Cross-context links and project index links use folder-prefix format (`[[folder/index|name]]`). Within-project links may use bare filenames where nearest-match resolves correctly.
**Why:** Wikilinks are path-agnostic — they resolve by filename regardless of folder structure, so moving a file doesn't break incoming links. The format must work in both Obsidian (nearest-match resolution) and Foam (shortest-unique-path resolution). (R1)
**Alternatives considered:** Standard markdown links — rejected; path-sensitivity makes them fragile during reorganization. Bare wikilinks everywhere including root-level files — rejected; Obsidian nearest-match does not apply from root level, creating silent wrong-resolution risk.

---

## D2 — 2026-04-25 — Conversation frontmatter as source of truth; indexes are generated artifacts

**Decision:** Conversation files carry metadata in YAML frontmatter (`title`, `projects`, `updated`). Index files are generated artifacts owned by CI — never edited manually.
**Why:** Tool-agnostic constraint: must work in both Obsidian and Foam without plugins. Dataview queries are Obsidian-only. Static generated files work everywhere. (R1, R7)
**Alternatives considered:** Dataview queries — rejected; Obsidian-only dependency. Bidirectional manual wikilinks — rejected; multiple files would drift out of sync.

---

## D1 — 2026-04-24 — `decisions.md` captures design history; `CLAUDE.md` captures operational state

**Decision:** CLAUDE.md files capture current rules and structure. `decisions.md` captures design history — why things are the way they are, what was tried and rejected.
**Why:** CLAUDE.md doesn't capture reasoning or evolution — it only reflects current state. Design rationale belongs in a separate artifact so CLAUDE.md stays concise and operational. (A3)
**Alternatives considered:** Embed decisions in CLAUDE.md — rejected; bloats operational instructions with historical context and makes both harder to maintain.
