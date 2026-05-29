# Ensures Python is installed, then delegates to setup.py.
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

& $python.Source "$repoRoot\_scripts\setup.py"
