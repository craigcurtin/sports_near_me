# sports_near_me

When do the teams you follow play next, and can you actually watch or listen?

```
$ sports-game nhl blackhawks
As of: Sunday, September 13, 2026  08:02 AM EDT - schedules can change after this.

Game: Chicago Blackhawks at Vegas Golden Knights
Kickoff: Tuesday, September 29, 2026  10:30 PM EDT
Venue:   T-Mobile Arena (Las Vegas, NV)
TV:      ESPN - national broadcast, every market gets this one.
Audio:   None listed in ESPN's data - that's a known gap, not evidence there isn't
         one. Your team's local flagship station/stream almost certainly still
         carries this regionally; check the team's own site/app if you need it.
         Verified regional flagship: WGN Radio 720 AM - https://wgnradio.com/blackhawks/blackhawks-live/
         Out-of-market listeners: https://tunein.com/radio/NHL-Radio--Stream-Hockey-Radio-c393481/
More at: https://www.espn.com/nhl/game/_/gameId/401891775/blackhawks-golden-knights
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
  silence at face value, a small **hand-verified table** of real regional
  flagships (Bears → WBBM, Cubs → WSCR, Blackhawks → WGN, Tennessee → the
  Vol Network - see `leagues/*.py`'s `KNOWN_AUDIO`) fills the gap for the
  teams checked so far. It's deliberately partial, not a guess at every
  team in every league - broadcast rights are real contracts that get
  renegotiated (the Cubs alone changed flagship stations three times in
  the last decade), so each entry needs periodic re-verification, not a
  "set once" assumption.
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
