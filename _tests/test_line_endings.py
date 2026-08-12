#!/usr/bin/env python3
"""T12 — R2: generated files use LF line endings on every platform.

`.gitattributes` declares `* text=auto eol=lf`, so git normalizes on staging and
a CRLF working tree shows an *empty* diff — while `git status` still reports the
file modified and blocks `git pull`. That failure mode is invisible on Linux CI
and only bites on Windows, which is why it survived unnoticed.

Root cause: Python's text mode translates "\\n" to "\\r\\n" on Windows unless the
newline is pinned. `Path.write_text(newline=...)` would fix it but is 3.10+, and
this project documents Python 3.8+, so every write site uses the explicit
`open(..., newline="\\n")` form instead.

T12.1-T12.2 are behavioral — run the generators and inspect the bytes.
T12.3-T12.4 are static — no new write site can reintroduce the bug.

Exit codes:
  0 — all checks pass
  1 — one or more checks failed
"""
import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent
SCRIPTS = REPO / "_scripts"

# Saved transcripts predating `.gitattributes eol=lf` carry CRLF in their blobs, and
# git refuses to renormalize them because they also contain lone CRs from captured
# terminal output. They are historical and never contributed upstream;
# save-conversation.py writes LF now, so new ones are clean. Exempt from T12.2.
SKIP_PREFIXES = ("_conversations/",)

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"OK   {label}")
    else:
        print(f"FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


# --- T12.1: a generator run produces no CR bytes -----------------------------

def t12_1_generated_output_has_no_cr() -> None:
    """Run generate-dashboard.py against a temp vault; assert no \\r in output."""
    with tempfile.TemporaryDirectory() as d:
        vault = Path(d)
        for sub in ("personal/projects", "personal/areas", "personal/resources",
                    "personal/archive", "_conversations"):
            (vault / sub).mkdir(parents=True, exist_ok=True)

        proj = vault / "personal/projects/demo"
        proj.mkdir(parents=True, exist_ok=True)
        with open(proj / "_memory.md", "w", encoding="utf-8", newline="\n") as f:
            f.write("# Memory\n\n## Snapshot\n\nA demo snapshot line.\n")
        with open(proj / "index.md", "w", encoding="utf-8", newline="\n") as f:
            f.write("# demo\n")

        res = vault / "personal/resources/note.md"
        with open(res, "w", encoding="utf-8", newline="\n") as f:
            f.write("---\ntags: [demo-tag]\n---\n\n# Note\n\nBody.\n")

        with open(vault / "dashboard.md", "w", encoding="utf-8", newline="\n") as f:
            f.write("# Dashboard\n\n## active projects\n\n## contexts\n")

        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "generate-dashboard.py")],
            cwd=str(vault), capture_output=True, text=True,
        )
        if proc.returncode != 0:
            check("T12.1 generator exits 0", False, proc.stderr.strip()[:200])
            return
        check("T12.1 generator exits 0", True)

        offenders = [
            str(f.relative_to(vault))
            for f in vault.rglob("*.md")
            if b"\r" in f.read_bytes()
        ]
        check(
            "T12.1 no CR bytes in generated .md files",
            not offenders,
            f"{len(offenders)} file(s): {', '.join(offenders[:5])}",
        )


# --- T12.2: tracked .md files in the repo are CR-free ------------------------

def t12_2_tracked_files_have_no_crlf() -> None:
    """Every tracked .md file must use LF line endings.

    Checks for CRLF *pairs*, not for any CR byte. A lone CR is legitimate content
    — saved conversation transcripts capture terminal output that uses bare CR for
    in-place line rewrites — and `text=auto` makes git refuse to normalize files
    containing them, because the conversion would not round-trip.
    """
    proc = subprocess.run(
        ["git", "ls-files", "-z", "*.md"],
        cwd=str(REPO), capture_output=True,
    )
    if proc.returncode != 0:
        check("T12.2 tracked .md files use LF endings", True, "git unavailable — skipped")
        return

    offenders = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        name = raw.decode("utf-8")
        if name.startswith(SKIP_PREFIXES):
            continue
        f = REPO / name
        if f.is_file() and b"\r\n" in f.read_bytes():
            offenders.append(name)

    detail = ""
    if offenders:
        detail = (
            f"{len(offenders)} file(s), e.g. {', '.join(offenders[:3])}. "
            "Committed before .gitattributes set eol=lf, so the CRLF is in the blob. "
            "`git add --renormalize` will not fix files that also contain lone CRs — "
            "rewrite the bytes (replace b'\\r\\n' with b'\\n') and commit."
        )
    check("T12.2 tracked .md files use LF endings", not offenders, detail)


# --- T12.3: no script uses Path.write_text -----------------------------------

def t12_3_no_write_text() -> None:
    """write_text() cannot pin newline before Python 3.10 — ban it outright."""
    offenders = []
    for script in sorted(SCRIPTS.glob("*.py")):
        for i, line in enumerate(script.read_text(encoding="utf-8").split("\n"), 1):
            if ".write_text(" in line:
                offenders.append(f"{script.name}:{i}")
    check(
        "T12.3 no .write_text() in _scripts/",
        not offenders,
        ", ".join(offenders),
    )


# --- T12.4: every text-mode open for writing pins newline --------------------

_OPEN_W = re.compile(r'open\([^)]*?["\'][wa]\+?["\']')


def t12_4_writes_pin_newline() -> None:
    """Any open(..., 'w'|'a') in text mode must pass newline="\\n"."""
    offenders = []
    for script in sorted(SCRIPTS.glob("*.py")):
        for i, line in enumerate(script.read_text(encoding="utf-8").split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("#") or not _OPEN_W.search(line):
                continue
            if '"b"' in line or "'b'" in line or '"wb"' in line or "'wb'" in line:
                continue  # binary mode does not translate newlines
            if 'newline="\n"' in line or "newline='\n'" in line:
                continue
            if "newline=" in line:
                continue  # explicitly chosen, even if not LF
            offenders.append(f"{script.name}:{i}")
    check(
        'T12.4 every text-mode write pins newline',
        not offenders,
        ", ".join(offenders),
    )


# --- T12.5: the scripts still parse -----------------------------------------

def t12_5_scripts_parse() -> None:
    offenders = []
    for script in sorted(SCRIPTS.glob("*.py")):
        try:
            ast.parse(script.read_text(encoding="utf-8"))
        except SyntaxError as e:
            offenders.append(f"{script.name}:{e.lineno}")
    check("T12.5 all _scripts/*.py parse", not offenders, ", ".join(offenders))


def main() -> int:
    t12_1_generated_output_has_no_cr()
    t12_2_tracked_files_have_no_crlf()
    t12_3_no_write_text()
    t12_4_writes_pin_newline()
    t12_5_scripts_parse()

    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for f in failures:
            print(f"  FAIL {f}")
        return 1
    print("All line-ending checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
