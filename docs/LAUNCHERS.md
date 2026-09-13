# sports-game-launchers(7)

Per-platform scripts that run [`sports-game`](CLI.md) without a manual install.

**Python itself must already be installed first** - these scripts bootstrap
everything *after* that (a virtual environment, this package), but none of
them installs Python. See the main [README's Prerequisites
section](../README.md#prerequisites) for how to check and install it on
macOS, Windows, or Linux.

| Platform | Script |
|---|---|
| macOS / Linux | `./scripts/sports-game.sh [args...]` |
| Windows (cmd.exe) | `scripts\sports-game.cmd [args...]` |
| PowerShell (Windows or cross-platform) | `./scripts/sports-game.ps1 [args...]` |

These three scripts are equivalent entry points into `sports-game` for
someone who doesn't want to run `pip install` by hand. Each one, on first
run only:

1. Creates a virtual environment at `.venv` next to the project root, if
   one isn't already there.
2. Installs this package into it (editable install), along with its one
   dependency, PyYAML.

On every run — first or subsequent — the script then execs `sports-game`
inside that virtual environment, forwarding every argument unchanged.
There's no functional difference between running a launcher script and
running `sports-game` directly after a manual `pip install -e .`; the
scripts exist purely so a non-technical user can double-click or run one
command on whichever platform they have, without knowing what a virtual
environment is.

## Usage

The argument forwarding means every `sports-game` invocation from
[CLI.md](CLI.md#examples) works identically through any launcher:

```bash
./scripts/sports-game.sh nfl bears
scripts\sports-game.cmd nfl bears
./scripts/sports-game.ps1 nfl bears
```

## Files

`.venv/` — the bootstrapped virtual environment. Safe to delete at any
time; the next launcher run recreates it.

## Platform notes

**`sports-game.sh`** — requires `python3` (or `python`) on `PATH`. Uses
`set -euo pipefail` so a setup failure stops the script rather than
falling through to a broken run.

**`sports-game.cmd`** — requires `python` on `PATH`. Each setup step is
checked; a failure prints a one-line hint about Python/PATH rather than a
raw traceback.

**`sports-game.ps1`** — works under both Windows PowerShell 5.1 and
cross-platform PowerShell 7+ (including on macOS/Linux, where it's a third
option alongside the `.sh` script). Detects the platform via `$env:OS`
rather than the newer `$IsWindows` automatic variable, since the latter
doesn't exist under Windows PowerShell 5.1.

## See also

[CLI.md](CLI.md) · [CONFIG.md](CONFIG.md) · [EXTENDING.md](EXTENDING.md)
