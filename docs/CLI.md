# sports-game(1)

Show when a followed team plays next, and how to watch or listen.

```
sports-game [shared-options] [sport [team]]
```

Looks up a team's next scheduled game (or a specific week's game) from
ESPN's public schedule data and prints kickoff time, venue, and how the
game is broadcast — television/streaming and radio, reported separately.

Covers ten leagues: NFL, MLB, NHL, NCAA football, NCAA men's and women's
basketball, NCAA baseball, NCAA men's hockey, and NCAA men's and women's
volleyball.

- Run with a **sport** and **team** for one specific lookup.
- Run with just a **sport** to show every team (and every team in every
  followed conference) from your config file's follow list for that sport.
- Run with **no arguments at all** to show your entire follow list across
  every sport.

Team names resolve loosely: a nickname, city, full team name, or league
abbreviation all work (`bears`, `chicago`, `"chicago bears"`, `CHI` are all
the Chicago Bears). A name that matches more than one team — e.g. `new york`,
which is both the Giants and the Jets — is refused with the list of real
matches rather than guessed at.

## Sports

| Key | League |
|---|---|
| `nfl` | National Football League |
| `mlb` | Major League Baseball — the only league where ESPN reports the real National/Home/Away broadcast split per game, see [Broadcast notes](#broadcast-notes) |
| `nhl` | National Hockey League |
| `ncaaf` | NCAA football |
| `ncaamb` | NCAA men's basketball |
| `ncaawb` | NCAA women's basketball |
| `ncaabsb` | NCAA baseball |
| `ncaamh` | NCAA men's hockey |
| `ncaavbw` | NCAA women's volleyball |
| `ncaavbm` | NCAA men's volleyball |

Every NCAA sport supports following a whole conference (see
[CONFIG.md](CONFIG.md)) — team and conference names for NCAA sports are
resolved against ESPN's live team/conference lists on every run, not a
hardcoded table, since a handful of hundred-plus-school sports would be
impractical to hand-maintain and conference realignment does happen.

## Options

| Flag | Meaning |
|---|---|
| `--config PATH` | YAML config file. Default: `~/.sports_near_me.yaml` if it exists; without it, only explicit `sport team` lookups work — there's no follow list to fall back to. |
| `--week N` | Show a specific week's game instead of the next upcoming one. Only meaningful for `nfl` and `ncaaf`; other sports ignore it. |
| `--tz ZONE` | IANA timezone for the printed kickoff time (e.g. `America/Chicago`). Default: this machine's local timezone. |
| `--log-dir DIR` | Also write a timestamped diagnostic log file under `DIR`, in addition to stderr. Diagnostics never appear in the report itself (stdout). |
| `--log-level LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Default: `INFO`. Mutually exclusive with `-v`/`-s`. |
| `-v`, `--verbose` | Shortcut for `--log-level DEBUG`. |
| `-s`, `--silent` | Shortcut for `--log-level ERROR` — only the report and real errors print. |

## Broadcast notes

The `TV:` line and `Radio:` line are always printed separately, whatever
ESPN reports for the game. Classification differs by league because the
underlying broadcast systems genuinely differ:

**NFL** — Flagship windows and streaming exclusives (NBC, ESPN/ABC, Prime
Video, NFL Network, Peacock, Netflix) are flagged as reaching every market.
FOX/CBS Sunday-window games can't be resolved to a specific market by this
tool — that depends on affiliate coverage maps this tool has no access to
(the sites that publish them block automated requests). Check the NFL
app's "Local" tab for those.

**MLB** — ESPN reports the actual National/Home/Away split per game, so
`sports-game` prints all of it directly — e.g. national streaming on
MLB.TV plus each team's own regional network. A note about MLB.TV's
blackout of both teams' home markets is appended when relevant.

**NCAA (all six sports) and NHL national games** — A conference or league
TV/streaming deal is one single nationally-distributed feed of that
specific game, not a regional split — you just need the matching
cable/streaming access.

**NHL non-national games** — ESPN's schedule data doesn't include
regional-sports-network coverage for most NHL games; an empty broadcast
line there means "check your team's local RSN or streaming app," not
"nothing airs."

## Exit status

- `0` — at least one game report was printed successfully.
- `1` — no team/sport was resolvable, the config file was invalid or
  missing when explicitly requested, or nothing could be shown at all.

## Examples

```bash
sports-game nfl bears                                # one team, directly
sports-game ncaaf "ohio state" --week 3               # a specific week
sports-game ncaaf                                     # everything you follow in NCAA football
sports-game                                           # your entire follow list, every sport
sports-game --config ~/work/sports.yaml mlb cubs      # a specific config file
```

## See also

[CONFIG.md](CONFIG.md) · [LAUNCHERS.md](LAUNCHERS.md) · [EXTENDING.md](EXTENDING.md)

Terminal man pages with the same content live in [`man/`](man/) — see
[man/README.md](man/README.md) for how to view them.
