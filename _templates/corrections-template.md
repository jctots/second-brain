<!--
Template: _self/corrections.md
Use: Copy to _self/corrections.md. `setup.py` does this automatically on a fresh clone.
Loaded via `@_self/corrections.md` in root CLAUDE.md — an import, not a hook, so it is
present in every request and survives /compact. There is no character cap on it, but
the content is in every request: a rule that never fires is costing you tokens.
Maintained by Claude via /remember. Rules are imperative, one line each.
-->

# Corrections — {your-name}

[[dashboard|⬅️ Dashboard]]

_AI-maintained. Updated via `/remember`. Do not manually edit._

## Communication

_How you want to be talked to. Terse rules, not paragraphs._

- Example: lead with the answer, no trailing summary.

## Tooling

_Environment facts Claude keeps getting wrong — paths, shells, what is read-only._

- Example: convert Windows paths to POSIX form before using them in Bash.

## Terminology

_Words you want corrected, and how._

## Known failure modes

_Only add when a mistake **repeats**. A single error is not a failure mode — it is an error. Keep each entry to three parts: a bolded name, one clause of cause, and a **How to apply** sentence that a future session can act on._

- **Name of the pattern.** What went wrong and how many times, in one clause. **How to apply:** the concrete check that would have caught it.
