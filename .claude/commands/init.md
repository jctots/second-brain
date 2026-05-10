Initialize a new vault entry (project, area, or resource). Execute in order:

1. **Gather context interactively** — ask open questions to understand what the user wants to create:
   - What is your goal or the purpose of this entry?
   - What are your inputs? (links, documents, existing notes, a brief, a repo — or ask Claude to research something)
   - Any other relevant context? (deadline, audience, related projects, constraints)

   Ask all three in one message. Wait for the user's response before proceeding.

   **After the user responds:**
   - If the user names an existing vault project as input or context, find it at `{context}/projects/{name}/` and read its `reference.md` and `_memory.md` before proposing classification.
   - If the user asks you to research inputs (APIs, public docs, existing repos), do that research now — before proposing classification. Findings will seed `reference.md`.

2. **Propose a classification** — based on the answers, propose:
   - **PARA category:** `projects` if there is a defined goal the user is still working toward; `areas` if it is an ongoing responsibility with no end date; `resources` if it is reference material or a topic of interest with no active work
   - **Context:** `personal` (default), `professional` (current employer / company work only), or `public` (intended for sharing or publishing)
   - **Slug:** kebab-case name derived from the goal (e.g. `rag-experiment`, `home-lab`, `para-method`)
   - **Description:** one sentence stating the goal or subject

   Present these as a confirmation block:
   ```
   Proposed:
   - Category: {para}
   - Context: {context}
   - Name: {slug}
   - Description: {description}

   Confirm, or tell me what to adjust.
   ```

   Wait for confirmation before creating any files. Accept both explicit confirmation ("yes", "go ahead") and implicit confirmation (user provides additional detail without pushing back on the classification).

3. **Prior art check** — if the project involves building or creating something (software, a tool, a script, an integration, a workflow system), before creating any files, search for existing open-source projects with the same goal. Search GitHub/GitLab and any registries relevant to the project type (package managers, extension stores, app directories, etc.) depending on what the user described.

   Present findings concisely:
   - What exists, how close it is, and what license it uses
   - Any meaningful gap between what exists and what the user described

   Then ask: *"Want to start from scratch, or build on one of these (fork/extend)?"*

   - If forking/extending: note the upstream repo as an input in `reference.md` and continue to file creation
   - If starting from scratch: continue directly

   Skip if the project is primarily organizational (job search, finances, health tracking, area management).

4. **Create files based on category:**

   **For `projects`** — create a folder `{context}/projects/{slug}/` with four files, using `_templates/`:

   | File | Template |
   |---|---|
   | `index.md` | `_templates/index-template.md` |
   | `CLAUDE.md` | `_templates/CLAUDE-template.md` |
   | `_memory.md` | `_templates/_memory-template.md` |
   | `reference.md` | `_templates/reference-template.md` |

   Placeholder replacements for all files:

   | Placeholder | Replace with |
   |---|---|
   | `{project-name}` | `{slug}` |
   | `YYYY-MM-DD` | today's date |
   | `context: personal \| professional \| public` | chosen context |
   | `para: projects \| areas \| resources \| archive` | `projects` |
   | Description placeholder lines | the confirmed description |

   Additional per-file substitutions:
   - `index.md`: replace description placeholder with user's description; leave `## relevant conversations` empty (no wikilinks — the conversation hasn't been saved yet); strip the HTML comment block at the top
   - `CLAUDE.md`: replace "What this project is" body with user's description; replace the project-specific guidance placeholder in "On sync memory" with `Strategy changes, tool choices, design tradeoffs; not routine implementation details.`; strip the HTML comment block at the top
   - `_memory.md`: replace Current status body with `Project initialized. No work started yet.`; strip the HTML comment block at the top
   - `reference.md`: replace `{Section}` heading and body with `## Brief` / description and confirmed inputs; if you researched inputs in step 1, populate the relevant sections now with findings (API schemas, setup notes, links) — do not leave research results as placeholders; strip the HTML comment block at the top

   **For `areas` or `resources`** — create a single file `{context}/{para}/{slug}.md` from `_templates/area-resource-template.md`:
   - Replace `{title}` with a title-cased version of the slug
   - Fill in `context`, `para`, and `created` fields
   - Add a one-line description below the dashboard link
   - Strip the HTML comment block at the top

5. **Update `dashboard.md`** — find the correct context section and PARA line, then append the new wikilink:
   - Projects: `[[{slug}/index|{slug}]]`
   - Areas and resources: `[[{slug}]]`
   - Separate from existing links with ` · `
   - If the line currently reads `—`, replace `—` with the wikilink

6. **Confirm** — list what was created, one line per file, plus the dashboard line updated.
