#!/usr/bin/env bash
# Launcher for macOS/Linux. Bootstraps a local .venv on first run (creating
# it, installing this package into it) so a friend who just cloned/copied
# this folder doesn't need to know anything about Python packaging - after
# that, every run just forwards straight through.
#
# Usage: ./scripts/sports-game.sh [sport] [team] [flags]
#   e.g. ./scripts/sports-game.sh nfl bears
#        ./scripts/sports-game.sh              (shows everything in your follow list)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"

if [ ! -x "$VENV/bin/python" ]; then
    echo "Setting up (first run only)..." >&2
    PYBIN="$(command -v python3 || command -v python)"
    "$PYBIN" -m venv "$VENV"
    "$VENV/bin/pip" install -q --upgrade pip
    "$VENV/bin/pip" install -q -e "$ROOT"
fi

exec "$VENV/bin/python" -m sports_near_me.cli "$@"
