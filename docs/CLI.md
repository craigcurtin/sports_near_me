# sports-game(1)

Show when a followed team plays next, and how to watch or listen.

```
sports-game [shared-options] [sport [team]]
```

Looks up a team's next scheduled game (or a specific week's game, or every
game in a rolling day window) from ESPN's public schedule data and prints
when the data was fetched, kickoff time, venue, and how the game is
broadcast — television/streaming and audio, reported separately, plus a
direct link to the game's ESPN page.

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
| `--week N` | Show a specific numbered week's game instead of the next upcoming one. Only meaningful for `nfl` and `ncaaf`; other sports ignore it. Mutually exclusive with `--range`. |
| `--range Nd` | Show every game in a rolling window starting today — `1d` is today only (including games already finished earlier today), `7d` is the next 7 days. By calendar date in the display timezone (see `--tz`). Can return more than one game for sports that play daily, e.g. MLB. Mutually exclusive with `--week`. |
| `--tz ZONE` | IANA timezone for the printed kickoff time (e.g. `America/Chicago`). Default: **UTC** - never guessed from this machine's own clock, since a config file can be copied to a different machine/location. Set this (or `tz:` in your config) to see local kickoff times, and to make `--range`'s day boundaries match your actual calendar day. |
| `--log-dir DIR` | Also write a timestamped diagnostic log file under `DIR`, in addition to stderr. Diagnostics never appear in the report itself (stdout). |
| `--log-level LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Default: `INFO`. Mutually exclusive with `-v`/`-s`. |
| `-v`, `--verbose` | Shortcut for `--log-level DEBUG`. |
| `-s`, `--silent` | Shortcut for `--log-level ERROR` — only the report and real errors print. |

## As-of timestamp

Every run prints an `As of:` line before any game reports, in the display
timezone. Schedules aren't static — weather postponements, doubleheaders,
and flexed games can all change a schedule after this data was fetched —
so this timestamp is what tells you how fresh the report is, not when you
happen to be reading it.

## Broadcast notes

The `TV:` line and `Audio:` line are always printed separately, whatever
ESPN reports for the game — called "Audio," not "Radio," since most of
what's listed here is consumed as internet audio today (team apps,
TuneIn), not strictly an AM/FM signal. A `More at:` line follows with a
direct link to the game's ESPN Gamecast page, when ESPN provides one — true
for every league checked so far. Broadcast classification differs by
league because the underlying systems genuinely differ:

**NFL** — Flagship windows and streaming exclusives (NBC, ESPN/ABC, Prime
Video, NFL Network, Peacock, Netflix) are flagged as reaching every market.
FOX/CBS Sunday-window games can't be resolved to a specific market by this
tool — that depends on affiliate coverage maps this tool has no access to
(the sites that publish them block automated requests). The note instead
points to [thesportsmaps.com/nfl](https://thesportsmaps.com/nfl/), a real,
verified county/zip-searchable coverage map, or the NFL app's "Local" tab.

**MLB** — ESPN reports the actual National/Home/Away split per game, so
`sports-game` prints all of it directly — e.g. national streaming on
MLB.TV plus each team's own regional network. A note about MLB.TV's
blackout of both teams' home markets is appended when relevant. When a
game has an audio entry, an extra block follows with a link to MLB's own
audio-streaming subscription and the official MLB App (both the iOS App
Store and Google Play listings) — useful for an out-of-market listener,
alongside the regional stations already listed for people in-market.

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
sports-game nfl bears                                 # one team, directly
sports-game ncaaf "ohio state" --week 3               # a specific numbered week
sports-game mlb cubs --range 1d --tz America/Chicago  # every Cubs game today
sports-game mlb cubs --range 7d --tz America/Chicago  # every Cubs game this week
sports-game ncaaf                                     # everything you follow in NCAA football
sports-game                                           # your entire follow list, every sport
sports-game --config ~/work/sports.yaml mlb cubs      # a specific config file
```

## See also

[CONFIG.md](CONFIG.md) · [LAUNCHERS.md](LAUNCHERS.md) · [EXTENDING.md](EXTENDING.md)

Terminal man pages with the same content live in [`man/`](man/) — see
[man/README.md](man/README.md) for how to view them.
