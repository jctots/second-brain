#!/usr/bin/env bash
# Setup script for Linux/macOS.
# Reads _infrastructure/stack.yaml and ensures the correct Python version and VS Code extensions are installed.
# Run from repo root: bash _scripts/setup.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA="$REPO_ROOT/_infrastructure/stack.yaml"

# --- parse Python version from _infrastructure/stack.yaml (no Python required at this stage) ---
REQUIRED_VERSION="$(grep -E '^\s+version:' "$INFRA" | head -1 | sed -E 's/.*version:[[:space:]]*"?([0-9]+\.[0-9]+[.0-9]*)"?.*/\1/')"
if [ -z "$REQUIRED_VERSION" ]; then
    echo "ERROR: could not read python.version from _infrastructure/stack.yaml"
    exit 1
fi
REQUIRED_MAJOR="${REQUIRED_VERSION%%.*}"
REQUIRED_MINOR="${REQUIRED_VERSION#*.}"
REQUIRED_MINOR="${REQUIRED_MINOR%%.*}"

echo "Required Python: $REQUIRED_VERSION"

# --- check installed Python ---
NEED_INSTALL=0
if command -v python3 &>/dev/null; then
    INSTALLED="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    echo "Found Python: $INSTALLED"
    INST_MAJOR="${INSTALLED%%.*}"
    INST_MINOR="${INSTALLED#*.}"
    if [ "$INST_MAJOR" -lt "$REQUIRED_MAJOR" ] || \
       { [ "$INST_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$INST_MINOR" -lt "$REQUIRED_MINOR" ]; }; then
        echo "Python $INSTALLED is below required $REQUIRED_VERSION."
        NEED_INSTALL=1
    fi
else
    echo "python3 not found."
    NEED_INSTALL=1
fi

if [ "$NEED_INSTALL" -eq 1 ]; then
    if command -v dnf &>/dev/null; then
        echo "Installing python3 via dnf..."
        sudo dnf install -y python3
    elif command -v apt-get &>/dev/null; then
        echo "Installing python3 via apt..."
        sudo apt-get install -y python3 python3-pip
    else
        echo "ERROR: no supported package manager (dnf, apt). Install Python $REQUIRED_VERSION manually."
        exit 1
    fi
fi

# --- pip dependencies ---
echo "Installing pip dependencies..."
python3 -m pip install --quiet -r "$REPO_ROOT/_scripts/requirements.txt"

# --- VS Code extensions ---
if command -v code &>/dev/null; then
    echo "Installing VS Code extensions..."
    # parse extension ids: lines matching "    - <id>" under vscode.extensions
    in_extensions=0
    while IFS= read -r line; do
        if echo "$line" | grep -qE '^\s+extensions:'; then
            in_extensions=1
            continue
        fi
        if [ "$in_extensions" -eq 1 ]; then
            if echo "$line" | grep -qE '^\s+-\s+\S'; then
                ext="$(echo "$line" | sed -E 's/.*-[[:space:]]+(.*)/\1/')"
                echo "  Installing extension: $ext"
                code --install-extension "$ext" --force 2>/dev/null || true
            else
                in_extensions=0
            fi
        fi
    done < "$INFRA"
else
    echo "VS Code (code) not in PATH — skipping extension install."
fi

echo "Setup complete."
