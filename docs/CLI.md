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
- Run with a **sport** and **several teams** to look them up in one run,
  without needing a config file - `sports-game ncaaf tennessee,wisconsin`,
  `tennessee, wisconsin` (space after the comma - no quoting needed;
  every shell token after the sport is rejoined before splitting), or
  even `tennessee wisconsin` (no comma at all) all work identically.
  Quoting is never required, just occasionally convenient. Each name
  resolves through the same rules as a single-team lookup, and the list
  is deduplicated by resolved team, so listing the same team two
  different ways only shows it once.
- Run with just a **sport** to show every team (and every team in every
  followed conference) from your config file's follow list for that sport.
- Run with **no arguments at all** to show your entire follow list across
  every sport.

Team names resolve loosely: a nickname, city, full team name, or league
abbreviation all work (`bears`, `chicago`, `"chicago bears"`, `CHI` are all
the Chicago Bears). A name that matches more than one team — e.g. `new york`,
which is both the Giants and the Jets — is refused with the list of real
matches rather than guessed at. This applies to each name in a
comma-separated list too - one bad or ambiguous name fails the whole
lookup with a clear error, rather than silently skipping it.

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
| `--week N` | Show a specific numbered week's game instead of the next upcoming one. Only `nfl` and `ncaaf` games carry a real week number — other sports report "no game found for week N" rather than showing anything, since there's no week number to match. Mutually exclusive with `--range`. |
| `--range Nd` | Show every game in a rolling window starting today — `1d` is today only (including games already finished earlier today), `7d` is the next 7 days. By calendar date in the display timezone (see `--tz`). Can return more than one game for sports that play daily, e.g. MLB. Mutually exclusive with `--week`. |
| `--tz ZONE` | IANA timezone for the printed kickoff time (e.g. `America/Chicago`). Default: **this machine's local timezone** - the zone actually used is always shown (e.g. `EDT`), never hidden. Set this (or `tz:` in your config) if you want a specific zone regardless of what machine runs the command - useful if a config file gets shared and run somewhere else. |
| `--log-dir DIR` | Also write a timestamped diagnostic log file under `DIR`, in addition to stderr. Diagnostics never appear in the report itself (stdout). |
| `--log-level LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Default: `INFO`. Mutually exclusive with `-v`/`-s`. |
| `-v`, `--verbose` | Shortcut for `--log-level DEBUG`. |
| `-s`, `--silent` | Shortcut for `--log-level ERROR` — only the report and real errors print. |
| `--explain` | Print what this run *would* do — which config file is in use, which sports/teams would be queried and whether each came from a CLI flag or the config's `follow:` list, and where every other setting (`--tz`, `--week`, etc.) came from — without contacting ESPN at all. See [below](#--explain-what-would-this-run-do). |

## `--explain`: what would this run do?

`--explain` answers "what is this actually going to do, and why" before it
does it — useful the first time you point `--config` at a new file, or
whenever a report doesn't look like what you expected and you want to
check whether a setting came from a flag you typed or from the config
file. It never resolves a team name against ESPN and never fetches a
schedule, so it's instant and works even if ESPN is down.

```
$ sports-game mlb cubs brewers --explain --silent
=== --explain: showing what this run would do - nothing was fetched from ESPN ===

Config file: /Users/craig/.sports_near_me.yaml  (existing file, loaded)

Setting    Value                        Source
tz         (not set)                    default
log_level  ERROR                        cli (--silent)
log_dir    (not set)                    default
week       (not set)                    default
range      (not set)                    default

Sports/teams this run would query:
  mlb: cubs, brewers
           source: cli (explicit team argument - overrides follow.mlb in the config for this run)
```

With no sport given at all, it walks every sport under the config's
`follow:` list — exactly what a real no-argument run would do — showing
each sport's configured teams and/or conferences (conference membership
itself isn't resolved, since that's a network call too):

```
$ sports-game --explain --silent
...
Sports/teams this run would query:
  nfl: teams: Bears
           source: config (follow.nfl.teams)
  mlb: teams: Cubs, Brewers
           source: config (follow.mlb.teams)
  ncaaf: teams: Tennessee
           source: config (follow.ncaaf.teams)
  ncaaf: conferences: SEC, Big Ten (membership not resolved in --explain)
           source: config (follow.ncaaf.conferences)
```

A sport with nothing configured and no team given on the command line is
reported as it would fail, not silently skipped:

```
  nhl: (nothing configured)
           would fail: no team given, and nothing under follow.nhl in the config
```

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
blackout of both teams' home markets is appended when relevant.

**NCAA (all six sports) and NHL national games** — A conference or league
TV/streaming deal is one single nationally-distributed feed of that
specific game, not a regional split — you just need the matching
cable/streaming access.

**Audio, specifically — ESPN's own data is confirmed incomplete.** A real
Bears game came back with zero audio entries despite WBBM actively
carrying every Bears game under a standing contract, so an empty `Audio:`
line reads as a hedge ("none listed in ESPN's data," not "nothing airs"),
and two more things follow it when known:

- **Verified regional flagship** — a small, hand-checked table
  (`KNOWN_AUDIO` in each league module) for teams actually verified so
  far: Bears→WBBM, Cubs→WSCR, Blackhawks→WGN, Tennessee football→the Vol
  Network. Deliberately partial, not a guess at every team — see
  [EXTENDING.md](EXTENDING.md) for why this needs periodic
  re-verification rather than one-time completion.
- **Out-of-market listeners** — each league's own standing national audio
  option(s) (`OUT_OF_MARKET_AUDIO`), shown for every game regardless of
  what ESPN reported: Westwood One + iHeartRadio for NFL, MLB Audio + the
  official app for MLB, TuneIn for NHL. Each entry was checked for both
  being real *and* actually free where claimed — TuneIn is free for every
  NHL game but paid-only for out-of-market NFL games in the US, which is
  exactly why NFL's list uses iHeartRadio instead of TuneIn.

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
sports-game ncaaf "tennessee,wisconsin"               # several teams, one run
sports-game ncaaf tennessee --week 3                  # a specific numbered week
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
