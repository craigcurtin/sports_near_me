# Documentation

| Doc | Covers |
|---|---|
| [CLI.md](CLI.md) | The `sports-game` command — sports, flags, broadcast-note behavior per league, exit status, examples |
| [CONFIG.md](CONFIG.md) | `~/.sports_near_me.yaml` — shared settings and the per-sport follow list (teams + conferences) |
| [LAUNCHERS.md](LAUNCHERS.md) | The `scripts/sports-game.{sh,cmd,ps1}` platform launchers |
| [EXTENDING.md](EXTENDING.md) | Architecture, how to add another league, the two real bugs found while building this (and the invariants that guard against them), and what's not built yet |

Terminal-native man pages with the same CLI/config/launcher content live
in [`man/`](man/), for viewing with `man`/`mandoc` instead of an editor —
see [man/README.md](man/README.md).
