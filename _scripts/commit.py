#!/usr/bin/env python3
# Git commit helper — pure mechanics. Commits staged changes, pulls with rebase, then pushes.
# Intended use: ask Claude to propose a message, then run this script.
#
# Usage:
#   python _scripts/commit.py -m "meta: migrate scripts to _scripts folder"
#   python _scripts/commit.py -m "project: update second-brain setup" -b "- add commit.py script\n- document workflow in CLAUDE.md"
#   python _scripts/commit.py --dry-run -m "chore: archive old notes"
#   python _scripts/commit.py --no-pull -m "meta: fix typo"  # skip pull if already up to date

import argparse
import subprocess
import sys


def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"error: {(result.stderr or result.stdout).strip()}")
        sys.exit(1)
    return result


def check_staged():
    result = run("git diff --cached --name-only")
    files = [f for f in result.stdout.strip().splitlines() if f]
    if not files:
        print("Nothing staged. Stage your changes first.")
        sys.exit(0)
    return files


# Paths/patterns whose unstaged changes are safe to discard — auto-updated by CI or hooks.
AUTO_UPDATED_PATHS = ("_conversations/",)
AUTO_UPDATED_PATTERNS = (
    r"^(personal|professional|public)/projects/[^/]+/index\.md$",
)


def is_auto_updated(filepath):
    import re
    if any(filepath.startswith(p) for p in AUTO_UPDATED_PATHS):
        return True
    return any(re.match(pat, filepath) for pat in AUTO_UPDATED_PATTERNS)


def discard_auto_unstaged(dry_run):
    """Discard unstaged changes in auto-updated paths so pull --rebase can proceed."""
    unstaged = [f for f in run("git diff --name-only").stdout.strip().splitlines() if f]
    if not unstaged:
        return

    auto = [f for f in unstaged if is_auto_updated(f)]
    manual = [f for f in unstaged if f not in auto]

    if manual:
        print("error: unstaged changes in the following files block pull:")
        for f in manual:
            print(f"  {f}")
        print("Stash or commit them first, then re-run.")
        sys.exit(1)

    if auto:
        if dry_run:
            print(f"[dry-run] would discard {len(auto)} auto-updated unstaged file(s):")
            for f in auto:
                print(f"  {f}")
            return
        print(f"Discarding {len(auto)} auto-updated unstaged file(s)...")
        for f in auto:
            subprocess.run(f"git checkout -- {f}", shell=True)


def pull_rebase(dry_run):
    discard_auto_unstaged(dry_run)
    if dry_run:
        print("[dry-run] would pull --rebase origin main")
        return
    print("Pulling with rebase...")
    result = subprocess.run(
        "git pull --rebase origin main",
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print("error: rebase failed — resolve conflicts then run again.")
        print(result.stdout.strip())
        print(result.stderr.strip())
        sys.exit(1)
    out = result.stdout.strip()
    if out and "up to date" not in out.lower():
        print(out)


def commit(message, dry_run):
    if dry_run:
        print(f"[dry-run] would commit:\n{message}")
        return
    msg_file = ".git/COMMIT_MSG_TMP"
    with open(msg_file, "w", encoding="utf-8") as f:
        f.write(message)
    run(f'git commit -F "{msg_file}"')
    import os; os.remove(msg_file)


def push(dry_run):
    if dry_run:
        print("[dry-run] would push origin main")
        return
    print("Pushing...")
    run("git push origin main")


def main():
    parser = argparse.ArgumentParser(
        description="Commit staged changes, pull with rebase, and push."
    )
    parser.add_argument("-m", "--message", required=True, help="Commit summary line")
    parser.add_argument("-b", "--body", default="", help="Commit body (optional, use \\n for line breaks)")
    parser.add_argument("--no-pull", action="store_true", help="Skip pull --rebase (use when already up to date)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without doing it")
    parser.add_argument("--repo", default=None, help="Path to target repo (for multi-root workspaces)")
    args = parser.parse_args()

    if args.repo:
        import os
        os.chdir(args.repo)

    body = args.body.replace("\\n", "\n").strip()
    full_message = f"{args.message}\n\n{body}" if body else args.message

    staged = check_staged()

    if args.dry_run:
        print(f"[dry-run] staged files ({len(staged)}):")
        for f in staged:
            print(f"  {f}")

    commit(full_message, args.dry_run)
    if not args.no_pull:
        pull_rebase(args.dry_run)
    elif args.dry_run:
        print("[dry-run] skipping pull (--no-pull)")
    push(args.dry_run)

    if not args.dry_run:
        print("Done.")


if __name__ == "__main__":
    main()
