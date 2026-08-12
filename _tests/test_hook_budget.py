#!/usr/bin/env python3
"""R6 — Verify hook-injected file sizes stay within per-file budget limits.

Claude Code caps a hook's entire *stdout* at 10,000 chars, not the file it reads.
Each injector prepends a label before the file body, so a file measured alone can
pass here and still be truncated live — this test therefore measures
`len(label) + len(file)`, and HOOK_BUDGET_HARD defaults to 9,000 to leave headroom.

A turn matching several projects puts every match under one cap. That case is not
enumerable here; `_hook_utils.emit_capped()` degrades the overflow to a pointer line
at injection time instead.

Exit codes:
  0 — all files within limit (warnings may be printed for files over 80%)
  1 — one or more files exceed the hard limit
"""
import sys
from pathlib import Path


def _load_dotenv(repo: Path) -> dict:
    env_file = repo / ".env"
    if not env_file.exists():
        return {}
    result = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def _budget_config(repo: Path) -> tuple[int, float]:
    env = _load_dotenv(repo)
    try:
        hard = int(env.get("HOOK_BUDGET_HARD", "9000"))
    except ValueError:
        hard = 9_000
    try:
        warn_pct = float(env.get("HOOK_BUDGET_WARN_PCT", "80"))
    except ValueError:
        warn_pct = 80.0
    return hard, warn_pct / 100.0


CONTEXTS = ["personal", "professional", "public"]

# ADVISORY: `_self/about.md` and `_self/corrections.md` are no longer hook output — root
# CLAUDE.md loads them with `@` imports, which have no character cap. They are still
# measured and warned on, because they sit in every request and size is a token cost,
# but they never fail the build and their absence is legal (a fresh clone has neither).
# They carry no injector label, so nothing is added to their length.


def project_label(filename: str, project: str, context: str) -> str:
    return f"Project {filename} auto-loaded for `{project}` ({context}/projects/):\n\n"


def summary_length(path: Path, label: str = "") -> int:
    return len(label) + len(path.read_text(encoding="utf-8"))


def check(label: str, n: int, failures: list, warnings: list, limit: int, warn_at: float) -> None:
    pct = n / limit
    if n > limit:
        print(f"FAIL {label}: {n}/{limit} chars ({pct:.0%})")
        failures.append(label)
    elif pct >= warn_at:
        print(f"WARN {label}: {n}/{limit} chars ({pct:.0%} — approaching limit)")
        warnings.append(label)
    else:
        print(f"OK   {label}: {n}/{limit} chars ({pct:.0%})")


def main() -> int:
    repo = Path(__file__).parent.parent
    LIMIT, WARN_AT = _budget_config(repo)
    failures: list[str] = []
    warnings: list[str] = []

    # Optional filter: python test_hook_budget.py personal/projects/my-project
    # Matches project path suffix; "all" or omitted runs everything.
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else None
    project_filter = None if (not filter_arg or filter_arg == "all") else filter_arg.strip("/")

    # A project filter scopes the run to that project — /remember step 2.5 uses the
    # exit code as its routing trigger, so vault-wide _self/ files must not decide it.
    if not project_filter:
        for self_file in ("about.md", "corrections.md"):
            f = repo / "_self" / self_file
            if f.exists():
                # Advisory only — never appended to `failures`. See ADVISORY note above.
                check(f"_self/{self_file}", summary_length(f), [], warnings, LIMIT, WARN_AT)

    for context in CONTEXTS:
        projects_dir = repo / context / "projects"
        if not projects_dir.exists():
            continue
        for project_dir in sorted(projects_dir.iterdir()):
            if not project_dir.is_dir() or project_dir.name.startswith("."):
                continue
            label_prefix = f"{context}/projects/{project_dir.name}"
            if project_filter and not label_prefix.endswith(project_filter.split("/")[-1]):
                continue
            for filename in ("CLAUDE.md", "_memory.md"):
                f = project_dir / filename
                if f.exists():
                    n = summary_length(f, project_label(filename, project_dir.name, context))
                    check(f"{label_prefix}/{filename}", n, failures, warnings, LIMIT, WARN_AT)

    print()
    if failures:
        print(f"{len(failures)} file(s) over hard limit — fix before merging:")
        for f in failures:
            print(f"  FAIL {f}")
        return 1

    if warnings:
        print(f"{len(warnings)} file(s) approaching limit (>{WARN_AT:.0%}) — consider trimming:")
        for w in warnings:
            print(f"  WARN {w}")

    if not failures and not warnings:
        print("All hook budgets within limits.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
