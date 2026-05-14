Search the vault by semantic similarity.

Usage: `/search <query>`

Run:
```
python _scripts/rag-search.py "$ARGUMENTS"
```

Then reformat the output as a numbered list. For each result:
- Make the file path a clickable markdown link: `[file/path.md](file/path.md)`
- Include the heading (if not `__preamble__`) after the link
- Show the score and snippet on the next line

Example format:
```
1. [personal/projects/home-lab-infrastructure/reference.md](personal/projects/home-lab-infrastructure/reference.md) § Backup targets on verona
   `0.57` — Proxmox VM snapshots — pushed from changi via PBS...
```

After the list, offer to open and summarize any of the results.

**Prerequisites:**
- Qdrant collection must be populated — run `python _scripts/rag-embed.py` first (or after significant vault changes)
- `OLLAMA_API_KEY` and `QDRANT_API_KEY` should be set in `.env` at vault root once keys are configured on braddell
