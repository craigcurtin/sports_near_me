# sports_near_me

When do the teams you follow play next, and can you actually watch or listen?

```
$ sports-game mlb "cubs,brewers"
As of: Sunday, September 13, 2026  08:39 AM EDT - schedules can change after this.

=== MLB: Chicago Cubs ===
Game: Chicago Cubs vs. Pittsburgh Pirates
Kickoff: Sunday, September 13, 2026  02:20 PM EDT
Venue:   Wrigley Field (Chicago, Illinois)
TV:      National: MLB.TV (Streaming) | Home broadcast: Marquee Sports Net (TV)  [MLB.TV
         blacks out both teams' home markets - if you're in one of those two, use the
         Home/Away channel listed instead.]
Audio:   None listed in ESPN's data - that's a known gap, not evidence there isn't
         one. Your team's local flagship station/stream almost certainly still
         carries this regionally; check the team's own site/app if you need it.
         Verified regional flagship: WSCR 670 The Score - https://www.audacy.com/670thescore
         Out-of-market listeners:
           MLB Audio subscription: https://www.mlb.com/live-stream-games/subscribe/mlb-audio
More at: https://www.espn.com/mlb/game/_/gameId/401816929/pirates-cubs

=== MLB: Milwaukee Brewers ===
Game: Milwaukee Brewers vs. Cincinnati Reds
Kickoff: Sunday, September 13, 2026  02:10 PM EDT
Venue:   American Family Field (Milwaukee, Wisconsin)
TV:      National: MLB.TV (Streaming) | Away broadcast: Reds.TV (Streaming) | Home
         broadcast: Brewers.TV (Streaming)  [MLB.TV blacks out both teams' home
         markets - if you're in one of those two, use the Home/Away channel instead.]
Audio:   None listed in ESPN's data - that's a known gap, not evidence there isn't
         one. Your team's local flagship station/stream almost certainly still
         carries this regionally; check the team's own site/app if you need it.
         Out-of-market listeners:
           MLB Audio subscription: https://www.mlb.com/live-stream-games/subscribe/mlb-audio
More at: https://www.espn.com/mlb/game/_/gameId/401816927/reds-brewers
```

A single run can look up several teams at once - `cubs,brewers`,
`cubs, brewers` (space after the comma is fine unquoted too), or even
`cubs brewers` (no comma at all) all work identically. Quoting is never
required, just occasionally convenient.

Ten leagues, one tool: **NFL, MLB, NHL, NCAA football, NCAA men's/women's
basketball, NCAA baseball, NCAA men's hockey, NCAA men's/women's volleyball.**

```bash
sports-game nfl bears
sports-game mlb "kansas city royals"
sports-game ncaaf tennessee
sports-game ncaawb wisconsin
sports-game ncaamh wisconsin
```

Team names resolve loosely - a nickname, city, full name, or abbreviation
all work, and any of these that uniquely identifies one team is enough:
`bears`, `chicago`, and `chicago bears` are all the same lookup, since
the Bears are the only NFL team in Chicago. Where a name genuinely isn't
unique (e.g. "New York" for NFL - Giants *and* Jets; "Chicago" for MLB -
Cubs *and* White Sox; "Duke" partially matching Duquesne/James Madison's
shared "Dukes" nickname), you get a clear error listing the real options
rather than a guess.

## Follow a list, not just one team

Set up `~/.sports_near_me.yaml` (copy [`config.example.yaml`](config.example.yaml))
with the teams and conferences you actually follow:

```yaml
follow:
  nfl:
    teams: [Bears, Packers]
  mlb:
    teams: [Cubs]
  ncaaf:
    teams: [Notre Dame]        # independent - not in any conference
    conferences: [SEC, Big Ten]   # Big Ten already includes Wisconsin
  ncaawb:
    teams: [Wisconsin]
  ncaamh:
    teams: [Wisconsin]
```

See [`config.example.yaml`](config.example.yaml) for the full example,
including women's volleyball and men's basketball too.

Then:

```bash
sports-game                   # every team/conference above, one game each
sports-game ncaaf             # just the NCAA football list
sports-game ncaaf wisconsin   # one specific team, ignoring the follow list
```

Following a conference follows each member team's **entire** schedule -
including non-conference and crossover games, not just games against other
conference members.

## What this can and can't tell you

- **Kickoff time, opponent, venue** - pulled live from ESPN's public
  schedule API, no API key needed.
- **An "As of" timestamp on every report.** Schedules change - weather
  postponements, doubleheaders, flexed games - so every run prints when
  the data was actually fetched, in the display timezone, right at the top.
- **TV/streaming and audio, shown separately, plus a direct link to the
  game's ESPN page** - every broadcast ESPN reports, split into a `TV:`
  line and an `Audio:` line (called "Audio," not "Radio" - most of what's
  listed here is consumed as internet audio today, not strictly AM/FM),
  followed by a `More at:` link straight to that game's ESPN Gamecast page.
- **MLB** gets the most precise answer of any league here: ESPN reports
  the real National/Home/Away broadcast split per game (e.g. "national
  streaming on MLB.TV" + "home broadcast: Marquee Sports Net" + "away
  broadcast: Nationals.TV"), including the MLB.TV blackout caveat for
  the two teams' home markets.
- **ESPN's own audio/radio data is confirmed incomplete** - a real Bears
  game came back with zero audio entries despite WBBM actively carrying
  every Bears game under a standing contract. Rather than take that
  silence at face value, a small **hand-verified table** (`KNOWN_AUDIO`
  in each `leagues/*.py` module) fills the gap for the teams checked so
  far:

  | Sport | Team | Flagship |
  |---|---|---|
  | NFL | Bears | WBBM Newsradio 780 AM / 105.9 FM |
  | NFL | Packers | 95.7 BIG FM (WRIT), Packers Radio Network |
  | NFL | Vikings | KFAN 100.3 FM (KFXN), Vikings Radio Network |
  | NFL | Chiefs | 96.5 The Fan (KFNZ) |
  | NFL | Lions | 97.1 The Ticket (WXYT), Lions Radio Network |
  | MLB | Cubs | WSCR 670 The Score |
  | MLB | White Sox | ESPN 1000 AM / 100.3 FM (WMVP) |
  | NHL | Blackhawks | WGN Radio 720 AM |
  | NCAA football | Tennessee | Vol Network |
  | NCAA football | Wisconsin | Wisconsin Badgers Sports Network |
  | NCAA men's basketball | Tennessee | Vol Network |
  | NCAA men's basketball | Wisconsin | Wisconsin Badgers Sports Network |
  | NCAA women's basketball | Tennessee | Vol Network |
  | NCAA women's basketball | Wisconsin | Wisconsin Badgers Sports Network |
  | NCAA baseball | Tennessee | Vol Network |
  | NCAA men's hockey | Wisconsin | Wisconsin Badgers Sports Network |
  | NCAA women's volleyball | Wisconsin | Wisconsin Badgers Sports Network |

  This is deliberately partial, not a guess at every team in every
  league - broadcast rights are real contracts that get renegotiated
  (the Cubs alone changed flagship stations three times in the last
  decade), so each entry needs periodic re-verification, not a "set
  once" assumption. **Know a team's real flagship that isn't listed
  here?** Verify it against a real source (the team's own site is
  usually best) and add it - see [docs/EXTENDING.md](docs/EXTENDING.md)
  for the pattern.
- **A separate, standing "out-of-market" list per league** (NFL →
  Westwood One + iHeartRadio, MLB → MLB Audio + the official app, NHL →
  TuneIn's NHL page) - useful because a team's own local stream can
  legally black out sports content for out-of-market listeners even
  while the AM/FM signal plays fine in its home market (confirmed: this
  is real, not hypothetical, for WGN's Blackhawks stream). Each option
  was checked for being both real *and* actually free where claimed -
  TuneIn is free for every NHL game but paid-only for out-of-market NFL
  games in the US, which is why NFL's list uses iHeartRadio instead.
  These apply to every game regardless of what ESPN's own audio data says.
- **NCAA** (all six sports) and **NHL** national broadcasts are flagged as
  a single nationally-distributed feed once you have the right cable/
  streaming access - not a regional-map question.
- **NFL's regional Sunday windows** get a real, verified pointer:
  [thesportsmaps.com](https://thesportsmaps.com/nfl/) publishes a live,
  searchable county/zip-level coverage map (checked and confirmed working
  before linking it here) - the closest thing to a real answer for "will
  I get this game," short of the NFL app's own "Local" tab.
- **What it still can't do**: resolve that FOX/CBS question itself, or
  give you a specific link for NHL's non-national games - ESPN's schedule
  data doesn't include regional-sports-network coverage at all for most
  of those, so an empty broadcast line there means "check your team's
  local RSN/app," not "nothing airs."

## Nothing here is a cached id

Team and conference names are resolved fresh against ESPN's live data on
every run - never cached, never written to the config file. NCAA
especially needed this: ESPN's own numeric team ids are the only reliable
way to route a schedule request there (abbreviation routing has real
collisions - confirmed `.../teams/osu/schedule` silently answers with a
small branch-campus team, not Ohio State), and if an id ever changed, the
next run just resolves against whatever's current. There's no stale
mapping anywhere to go wrong.

## If something breaks

ESPN's API isn't under this project's control, and it has already
changed shape more than once while building this tool. If a fetch ever
fails - a stale id, a renamed field, ESPN's API being down - the error
message names the exact URL involved, what the tool was trying to do,
and which file likely needs a look, instead of a bare traceback with no
indication of where the problem is. See
[docs/EXTENDING.md](docs/EXTENDING.md#failing-loud-every-espn-call-goes-through-fetchpy)
for how that's wired up, if you're digging into a fix yourself.

## Prerequisites

This is a Python tool. **Before anything else, Python 3.9 or newer needs
to be installed on the machine that will run it** - the launcher scripts
below handle everything after that automatically (setting up their own
environment, installing this package), but none of them can install
Python itself.

Check whether it's already there:

```bash
python3 --version   # macOS / Linux
python --version    # Windows
```

If that prints `Python 3.9` or higher, skip ahead to Install - nothing
else to do here.

If it's missing (or too old):

- **macOS**: install from [python.org/downloads](https://www.python.org/downloads/),
  or `brew install python3` if you use Homebrew. Recent macOS versions
  don't ship a usable Python by default.
- **Windows**: install from [python.org/downloads](https://www.python.org/downloads/).
  **Check "Add python.exe to PATH"** during setup - this is the single
  most common thing people miss, and without it none of the commands in
  this README will work from a fresh terminal.
- **Linux**: almost always already installed - run the `python3 --version`
  check above to confirm. If it's missing, use your distro's package
  manager, e.g. `sudo apt install python3 python3-venv` on Debian/Ubuntu
  (the separate `python3-venv` package matters - some minimal Linux
  installs leave it out, and the launcher scripts need it) or
  `sudo dnf install python3` on Fedora.

Once Python itself is confirmed working, everything below - the launcher
scripts especially - just works.

## Install

```bash
pip install -e .
```

Or use one of the launcher scripts in `scripts/` (see below) - they set up
their own virtual environment on first run, so no manual `pip install` step
is needed at all.

## Usage

```bash
sports-game <sport> <team>
sports-game <sport> <team>,<team>          # several teams, one run - no config file needed
sports-game <sport> <team> --week 5        # a numbered week - football only
sports-game <sport> <team> --range 1d      # every game today (incl. already finished)
sports-game <sport> <team> --range 7d      # every game in the next 7 days
sports-game <sport> <team> --tz America/Chicago
sports-game <sport> <team> --verbose       # DEBUG-level diagnostics on stderr
sports-game <sport> <team> --silent        # only the report and real errors
sports-game <sport> <team> --log-dir ~/logs
sports-game --config path/to.yaml <sport>  # use a specific config file
```

Sports: `nfl`, `mlb`, `nhl`, `ncaaf`, `ncaamb`, `ncaawb`, `ncaabsb`,
`ncaamh`, `ncaavbw`, `ncaavbm`.

`--week` and `--range` are mutually exclusive - each is a different way of
picking which game(s) to show; the default with neither is just the single
next upcoming game. `--range` accepts a number of days with an optional
`d` suffix (`1d`, `7d`, `10`, ...), always starting today.

`--tz` accepts any IANA timezone name; it defaults to **this machine's
local timezone** - most people run this from wherever they actually are,
and the zone actually used is always shown (e.g. "EDT"), never hidden.
Set `--tz` (or `tz:` in the config) if you want a specific zone regardless
of what machine runs the command. `--verbose`/`--silent`/
`--log-dir` never change the report itself (stdout) - only how much
diagnostic detail goes to stderr/a log file.

## Launcher scripts (for friends who don't want to touch Python)

Python itself still has to be installed first - see
[Prerequisites](#prerequisites) above; these scripts handle everything
after that. `scripts/` has one launcher per platform - each bootstraps
its own `.venv` on first run (creating it and installing this package)
and just forwards every argument after that:

| Platform | Script |
|---|---|
| macOS / Linux | `./scripts/sports-game.sh nfl bears` |
| Windows (cmd.exe) | `scripts\sports-game.cmd nfl bears` |
| Windows / cross-platform PowerShell | `./scripts/sports-game.ps1 nfl bears` |

## Run the tests

```bash
pip install pytest
pytest
```

## Documentation

Full docs, including the config file reference and notes on extending
this to another league, live in [`docs/`](docs/) — start at
[docs/README.md](docs/README.md). Man pages for the CLI, config file, and
launcher scripts are in [`docs/man/`](docs/man/).
