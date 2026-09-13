# sports_near_me

When do the teams you follow play next, and can you actually watch or listen?

```
$ sports-game mlb cubs
Game: Chicago Cubs vs. Pittsburgh Pirates
Kickoff: Sunday, September 13, 2026  02:20 PM EDT
Venue:   Wrigley Field (Chicago, Illinois)
TV:      National: MLB.TV (Streaming) | Home broadcast: Marquee Sports Net (TV)  [MLB.TV
         blacks out both teams' home markets - if you're in one of those two, use the
         Home/Away channel listed instead.]
Radio:   No radio broadcast listed.
```

Ten leagues, one tool: **NFL, MLB, NHL, NCAA football, NCAA men's/women's
basketball, NCAA baseball, NCAA men's hockey, NCAA men's/women's volleyball.**

```bash
sports-game nfl bears
sports-game mlb "kansas city royals"
sports-game ncaaf "ohio state"
sports-game ncaawb duke
```

Team names resolve loosely - a nickname, city, full name, or abbreviation
all work. Ambiguous names (e.g. "New York" for NFL, "Duke" partially
matching Duquesne/James Madison's shared "Dukes" nickname) raise a clear
error listing the real options rather than guessing.

## Follow a list, not just one team

Set up `~/.sports_near_me.yaml` (copy [`config.example.yaml`](config.example.yaml))
with the teams and conferences you actually follow:

```yaml
follow:
  nfl:
    teams: [Bears]
  mlb:
    teams: [Cubs]
  ncaaf:
    teams: [Notre Dame]        # independent - not in any conference
    conferences: [SEC, Big Ten]
  ncaamb:
    conferences: [ACC]          # every ACC team, e.g. Duke, UNC, Louisville...
```

Then:

```bash
sports-game                 # every team/conference above, one game each
sports-game ncaaf           # just the NCAA football list
sports-game ncaaf "auburn"  # one specific team, ignoring the follow list
```

Following a conference follows each member team's **entire** schedule -
including non-conference and crossover games, not just games against other
conference members.

## What this can and can't tell you

- **Kickoff time, opponent, venue** - pulled live from ESPN's public
  schedule API, no API key needed.
- **TV/streaming and radio, shown separately** - every broadcast ESPN
  reports for the game, split into a `TV:` line and a `Radio:` line.
- **MLB** gets the most precise answer of any league here: ESPN reports
  the real National/Home/Away broadcast split per game (e.g. "national
  streaming on MLB.TV" + "home broadcast: Marquee Sports Net" + "away
  broadcast: Nationals.TV"), including the MLB.TV blackout caveat for
  the two teams' home markets.
- **NCAA** (all six sports) and **NHL** national broadcasts are flagged as
  a single nationally-distributed feed once you have the right cable/
  streaming access - not a regional-map question.
- **What it can't do**: tell you whether a specific NFL FOX/CBS Sunday-
  window game reaches *your* zip code. That depends on affiliate-level
  regional broadcast maps that differ market by market, and the sites
  that publish those maps (506sports.com and similar) block automated
  requests - the NFL app's "Local" tab is the reliable source for that
  one case. NHL is similar in spirit: ESPN's schedule data doesn't
  include regional-sports-network coverage at all for most non-national
  games, so an empty broadcast there means "check your team's local
  RSN/app," not "nothing airs."

## Nothing here is a cached id

Team and conference names are resolved fresh against ESPN's live data on
every run - never cached, never written to the config file. NCAA
especially needed this: ESPN's own numeric team ids are the only reliable
way to route a schedule request there (abbreviation routing has real
collisions - confirmed `.../teams/osu/schedule` silently answers with a
small branch-campus team, not Ohio State), and if an id ever changed, the
next run just resolves against whatever's current. There's no stale
mapping anywhere to go wrong.

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
sports-game <sport> <team> --week 5        # football only; other sports ignore this
sports-game <sport> <team> --tz America/Chicago
sports-game <sport> <team> --verbose       # DEBUG-level diagnostics on stderr
sports-game <sport> <team> --silent        # only the report and real errors
sports-game <sport> <team> --log-dir ~/logs
sports-game --config path/to.yaml <sport>  # use a specific config file
```

Sports: `nfl`, `mlb`, `nhl`, `ncaaf`, `ncaamb`, `ncaawb`, `ncaabsb`,
`ncaamh`, `ncaavbw`, `ncaavbm`.

`--tz` accepts any IANA timezone name; it defaults to your machine's local
timezone. `--verbose`/`--silent`/`--log-dir` never change the report itself
(stdout) - only how much diagnostic detail goes to stderr/a log file.

## Launcher scripts (for friends who don't want to touch Python)

`scripts/` has one launcher per platform - each bootstraps its own
`.venv` on first run (creating it and installing this package) and just
forwards every argument after that:

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
