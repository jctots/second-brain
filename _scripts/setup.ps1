# Setup script for Windows.
# Reads _infrastructure/stack.yaml and ensures the correct Python version and VS Code extensions are installed.
# Run from repo root: .\_scripts\setup.ps1

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path $PSScriptRoot -Parent
$infra = "$repoRoot\_infrastructure\stack.yaml"
$infraContent = Get-Content $infra -Raw

# --- parse Python version from _infrastructure/stack.yaml ---
if ($infraContent -notmatch 'version:\s*"?(\d+\.\d+[\.\d]*)"?') {
    Write-Error "Could not read python.version from _infrastructure/stack.yaml"
    exit 1
}
$requiredVersion = $Matches[1]
$parts = $requiredVersion -split '\.'
$requiredMajor = [int]$parts[0]
$requiredMinor = [int]$parts[1]

Write-Host "Required Python: $requiredVersion"

# --- check installed Python ---
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }

$needInstall = $true
if ($python) {
    $installed = & $python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    if ($installed -match '(\d+)\.(\d+)') {
        Write-Host "Found Python: $installed"
        $instMajor = [int]$Matches[1]
        $instMinor = [int]$Matches[2]
        if ($instMajor -gt $requiredMajor -or ($instMajor -eq $requiredMajor -and $instMinor -ge $requiredMinor)) {
            $needInstall = $false
        } else {
            Write-Host "Python $installed is below required $requiredVersion."
        }
    }
}

if ($needInstall) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Installing Python $requiredVersion via winget..."
        winget install --id "Python.Python.$requiredMajor" --accept-source-agreements --accept-package-agreements
        Write-Host "Restart your terminal to update PATH, then re-run this script."
        exit 0
    } else {
        Write-Error "winget not available. Install Python $requiredVersion manually: https://www.python.org/downloads/"
        exit 1
    }
}

# --- pip dependencies ---
Write-Host "Installing pip dependencies..."
& $python.Source -m pip install --quiet -r "$repoRoot\_scripts\requirements.txt"

# --- VS Code extensions ---
$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if ($codeCmd) {
    Write-Host "Installing VS Code extensions..."
    $inExtensions = $false
    foreach ($line in (Get-Content $infra)) {
        if ($line -match '^\s+extensions:') { $inExtensions = $true; continue }
        if ($inExtensions) {
            if ($line -match '^\s+-\s+(\S+)') {
                $ext = $Matches[1]
                Write-Host "  Installing extension: $ext"
                & code --install-extension $ext --force 2>$null
            } elseif ($line -match '^\S' -or ($line -match '^\s+\S' -and $line -notmatch '^\s+-')) {
                $inExtensions = $false
            }
        }
    }
} else {
    Write-Host "VS Code (code) not in PATH — skipping extension install."
}

Write-Host "Setup complete."
