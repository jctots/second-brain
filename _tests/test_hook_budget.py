#!/usr/bin/env python3
"""R6 — Verify hook-injected file sizes stay within per-file budget limits.

Each hook command has an independent ~10k char cap before Claude Code redirects
output to a file reference instead of injecting it directly. Hard limit is 10,000
chars per file; warn at 8,000 (80%); consolidation target is 5,000 chars.

Exit codes:
  0 — all files within limit (warnings may be printed for files over 80%)
  1 — one or more files exceed the hard limit
"""
import sys
from pathlib import Path

LIMIT = 10_000      # hard limit per file — CI fails above this
WARN_AT = 0.80      # warn when file reaches 80% of limit (8,000 chars)
CONTEXTS = ["personal", "professional", "public"]


def summary_length(path: Path) -> int:
    return len(path.read_text(encoding="utf-8"))


def check(label: str, n: int, failures: list, warnings: list) -> None:
    pct = n / LIMIT
    if n > LIMIT:
        print(f"FAIL {label}: {n}/{LIMIT} chars ({pct:.0%})")
        failures.append(label)
    elif pct >= WARN_AT:
        print(f"WARN {label}: {n}/{LIMIT} chars ({pct:.0%} — approaching limit)")
        warnings.append(label)
    else:
        print(f"OK   {label}: {n}/{LIMIT} chars ({pct:.0%})")


def main() -> int:
    repo = Path(__file__).parent.parent
    failures: list[str] = []
    warnings: list[str] = []

    # Optional filter: python test_r6_hook_budget.py personal/projects/my-project
    # Matches project path suffix; "all" or omitted runs everything.
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else None
    project_filter = None if (not filter_arg or filter_arg == "all") else filter_arg.strip("/")

    for self_file in ("about.md", "rules.md"):
        f = repo / "_self" / self_file
        if f.exists():
            check(f"_self/{self_file}", summary_length(f), failures, warnings)
        else:
            print(f"FAIL _self/{self_file}: not found")
            failures.append(f"_self/{self_file} missing")

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
                    check(f"{label_prefix}/{filename}", summary_length(f), failures, warnings)

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
