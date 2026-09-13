@echo off
REM Launcher for Windows cmd.exe. Bootstraps a local .venv on first run
REM (creating it, installing this package into it) so a friend who just
REM copied this folder doesn't need to know anything about Python
REM packaging - after that, every run just forwards straight through.
REM
REM Usage: scripts\sports-game.cmd [sport] [team] [flags]
REM   e.g. scripts\sports-game.cmd nfl bears
REM        scripts\sports-game.cmd              (shows everything in your follow list)

setlocal
set "ROOT=%~dp0.."
set "VENV=%ROOT%\.venv"

if not exist "%VENV%\Scripts\python.exe" (
    echo Setting up ^(first run only^)... 1>&2
    python -m venv "%VENV%" || goto :error
    "%VENV%\Scripts\python.exe" -m pip install -q --upgrade pip || goto :error
    "%VENV%\Scripts\python.exe" -m pip install -q -e "%ROOT%" || goto :error
)

"%VENV%\Scripts\python.exe" -m sports_near_me.cli %*
exit /b %ERRORLEVEL%

:error
echo Setup failed - is Python installed and on PATH? 1>&2
exit /b 1
