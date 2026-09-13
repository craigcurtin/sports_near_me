# Launcher for PowerShell (Windows PowerShell 5.1 or PowerShell 7+, incl.
# on macOS/Linux). Bootstraps a local .venv on first run so a friend who
# just copied this folder doesn't need to know anything about Python
# packaging - after that, every run just forwards straight through.
#
# Usage: ./scripts/sports-game.ps1 <sport> <team> [flags]
#   e.g. ./scripts/sports-game.ps1 nfl bears
#        ./scripts/sports-game.ps1              (shows everything in your follow list)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv"
$OnWindows = ($env:OS -eq "Windows_NT")
$VenvPython = if ($OnWindows) { Join-Path $Venv "Scripts\python.exe" } else { Join-Path $Venv "bin/python" }

if (-not (Test-Path $VenvPython)) {
    Write-Host "Setting up (first run only)..."
    $PyLauncher = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }
    & $PyLauncher -m venv $Venv
    & $VenvPython -m pip install -q --upgrade pip
    & $VenvPython -m pip install -q -e $Root
}

& $VenvPython -m sports_near_me.cli @args
exit $LASTEXITCODE
