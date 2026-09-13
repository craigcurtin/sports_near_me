# Extending sports_near_me

Architecture notes for adding another league, plus ideas for what isn't
built yet. Written for whoever (human or Claude) picks this project back
up later without the context of building it.

## How the pieces fit together

```
sports_near_me/
  fetch.py           shared HTTP+JSON fetch - DataSourceError, fetch_json(),
                      parse_error() - see "Failing loud" below
  espn.py            generic schedule fetch - Game/Broadcast dataclasses,
                      next_game()/game_for_week(), the season-retry guard
  resolve.py          generic "name -> one Team, or a clear ambiguity error"
  dynamic_teams.py     NCAA team-list fetch (per sport/league, live, cached
                      only for the current process)
  conferences.py        NCAA conference name -> member teams (same live/
                      per-process-cache pattern)
  leagues/
    nfl.py, mlb.py, nhl.py     static 30-32 team tables (abbreviations
                                route directly - no numeric-id lookup needed)
    _ncaa.py                    ONE shared implementation for all six NCAA
                                sports - see "Adding an NCAA sport" below
    __init__.py                  the LEAGUES registry every CLI subcommand
                                and the config's follow list resolve against
  cli_common.py         YAML config loading + logging setup
  cli.py                 argparse subcommands, the follow-all/follow-one-
                      sport/explicit-team dispatch, the printed report
```

Every league module (or `_ncaa.NcaaLeague` instance) presents the same
four-method surface `cli.py` calls through, regardless of whether the
implementation is a hardcoded table or a live API call:

- `resolve_team(query) -> Team`
- `broadcast_note(game) -> str`
- `resolve_conf(query) -> Team` (NCAA only - `hasattr()`-checked in cli.py)
- `conf_members(conference_id) -> list[Team]` (NCAA only)

## Failing loud: every ESPN call goes through `fetch.py`

ESPN's API is not under this project's control, and it has already
changed shape on us more than once while building this (NCAA
abbreviation routing collisions, the season-parameter inconsistency, a
school's numeric id differing per sport). A stale id, a renamed JSON
field, or an endpoint that starts 404ing needs to be diagnosable from the
error message alone - nobody should have to re-derive "which URL, which
file, which field" from a bare traceback.

**The rule for any new fetch code: never call `urllib`/`json` directly.**
Go through `fetch.py`'s two pieces instead:

- **`fetch_json(url, context)`** - wraps the HTTP request and JSON
  parse. Any failure (unreachable host, non-2xx response, invalid JSON)
  raises `DataSourceError` naming the URL, `context` (a short string
  describing what this call was trying to do - "fetching nfl schedule
  for team_id=CHI"), and a pointer to which kind of file usually builds
  that URL (a `leagues/*.py` module, `dynamic_teams.py`, or
  `conferences.py`).
- **`parse_error(context, url, exception)`** - call this at the point a
  `KeyError`/`IndexError`/`TypeError` fires while walking an
  *already-parsed* JSON dict (`fetch_json` succeeded, but the shape
  wasn't what the code expected - a renamed/removed field). Wrap your
  parsing loop's body in `try: ... except (KeyError, IndexError,
  TypeError) as e: raise parse_error(context, url, e) from e` - see
  `espn.py`'s `_parse_events()` for the pattern.

Both keep the original exception chained (`from e`), so `__cause__`
still has the raw traceback for anyone who wants it - the wrapping adds
a breadcrumb, it doesn't hide anything.

**In `cli.py`**, every call site that can reach one of these (fetching a
schedule, resolving a team/conference name) catches `DataSourceError`
specifically and routes it through `_report_data_source_error()`, which
does two things: logs the full traceback (`logger.exception`, reaches
`--log-dir` if set) and prints the breadcrumb message itself to stderr
via `print(f"error: {e}", ...)` - so the actionable summary is always on
screen, not only in a log file someone has to go find. A genuinely
unexpected exception (a real bug, not a data-source problem) still gets
caught and logged, but is labeled "unexpected failure," not folded into
the same message shape - the two are worth telling apart on sight.

If you add a new module that calls an ESPN endpoint directly, route it
through `fetch_json()`/`parse_error()` the same way, and add a
`DataSourceError` catch at whatever `cli.py` call site reaches it. Tests
for the wrapping behavior itself (not just "it still works") live in
`tests/test_fetch.py`, `tests/test_dynamic_teams.py`, and
`tests/test_conferences.py` - follow that pattern (mock `fetch_json` to
return a malformed-but-valid dict, assert the raised `DataSourceError`'s
message names the right context) for anything new.

## Adding a pro league with a fixed team count (NBA, WNBA, MLS, ...)

Copy `leagues/nhl.py` - it's the simplest pattern (no MLB-style
Home/Away broadcast split, no NFL-style regional-window caveat):

1. Confirm the ESPN sport/league path segments (e.g. `basketball`/`nba`)
   and that `.../teams/{abbr}/schedule` routes correctly by abbreviation -
   check this by hand before writing code (see "Verify the API shape
   first" below). NFL/MLB/NHL all route cleanly this way; don't assume a
   new league will.
2. Fetch that league's real `/teams` list once (`curl` is fine) to build
   the static `_RAW_TEAMS` table with real abbreviations - don't
   hand-type them from memory.
3. Check whether the league's broadcasts need MLB-style Home/Away
   handling or NFL-style regional-window handling, or NHL's simpler
   "national or nothing ESPN reports" case. This is a real per-league
   judgment call, not something to guess generically - see
   `leagues/mlb.py`'s and `leagues/nfl.py`'s docstrings for why their
   answers differ.
4. Register it in `leagues/__init__.py`'s `LEAGUES` dict.
5. Add it to `add_shared_flags`'s subparser loop - nothing to do, that
   loop already iterates `LEAGUES`.

## Adding an NCAA sport (soccer, lacrosse, wrestling, ...)

This is now a two-line addition, not a new file:

```python
# leagues/__init__.py
ncaasoc = NcaaLeague("soccer", "mens-college-soccer")
LEAGUES["ncaasoc"] = ncaasoc
```

`_ncaa.py`'s `NcaaLeague` already handles team resolution (dynamic, via
`dynamic_teams.py`), conference resolution (via `conferences.py`), and
broadcast classification (the "single national feed, not a regional map"
answer that's genuinely correct for every NCAA sport checked so far).

**Verify the sport/league path segments first** - `curl
"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams?limit=400"`
and confirm it returns real teams before wiring it in. ESPN's naming isn't
fully predictable (`mens-college-basketball` and `college-baseball` don't
follow the same pattern; volleyball needed both `mens-college-volleyball`
and `womens-college-volleyball` checked separately).

## Two real bugs found building this - don't reintroduce them

Both were caught by testing against live data, not by reasoning about the
code - a reminder to actually run new leagues against real teams before
calling them done, not just unit-test the pure logic.

**Numeric id vs. abbreviation mismatch.** NFL/MLB/NHL teams resolve to
their abbreviation (`Team.id = "CHC"`); ESPN's per-game competitor data
uses a numeric id (`"16"`). A real Cubs–Pirates game printed as "Chicago
Cubs at Chicago Cubs" before `Game` was fixed to store *both* forms
(`home_id`/`home_abbr`) and `is_home_for()` was fixed to check either. A
new pro league added by copying `nhl.py` inherits this fix automatically
- don't reimplement `is_home_for()`/`opponent_name_for()` yourselves.

**Season-parameter guessing needs a truth check, not just a non-empty
response.** ESPN's schedule endpoint silently defaults to the wrong
season for some sports, and NCAA sports don't even agree whether
`season=2026` means the year a season *starts* or *ends*. The first fix
attempt retried with a guessed season and trusted any non-empty result -
which briefly made Duke men's basketball's schedule show its
already-*finished* 2025-26 season as if it were current, a worse failure
than the honest "no upcoming game" it was replacing. `espn.py`'s
`_has_upcoming_event()` guard exists specifically to catch this: a
retried season is only trusted if it actually contains a future,
uncompleted game. Any new season-related logic should keep that shape
(verify the *content* is useful, not just that the request succeeded).

## Why nothing is ever cached as an id

`dynamic_teams.py` and `conferences.py` both cache results only for the
lifetime of one process (a plain module-level dict), and neither is ever
written to the config file or any other on-disk location. This is
deliberate, not an oversight: if ESPN ever changes a school's numeric id
or a conference's group id, the very next run resolves against whatever
id is current - there's no stale mapping anywhere that could go wrong.
Any future caching (see below) needs a TTL or explicit invalidation, not
a "resolve once, remember forever" scheme - that's exactly the persisted-
id failure mode this design avoids today.

## Already built, beyond the original single-game lookup

Worth noting here since they didn't exist in the first version and might
otherwise look missing to someone skimming this file:

- **`--range Nd`** (`espn.games_within()`) - every game in a rolling
  window from today, by calendar date in the *display* timezone (see the
  next point for what that defaults to). `--week N` still exists
  separately for a numbered week; the two are mutually exclusive.
- **Local-by-default, never-HIDDEN timezone.** `cli._display_tz()`
  defaults to this machine's own local timezone - the first version of
  this defaulted to UTC instead, reasoning that a config file (and its
  follow list) can travel to a different machine/location, so guessing
  local time could be wrong. That traded a real problem (most people
  don't want to hand-convert UTC to local time) for a rare one (the
  machine's clock isn't where the viewer is) - reverted once that
  tradeoff was pointed out. What actually matters, and is still true:
  the zone in use is never hidden (`%Z` on every kickoff line), and
  `--tz`/config `tz` are always there for the rare case where the
  machine's own zone genuinely isn't what you want.
- **An `As of:` timestamp on every report** - schedules change (weather,
  doubleheaders, flexed games), so every run states when the data was
  actually fetched, not just what it fetched.
- **A direct per-game link** (`Game.link`, from ESPN's own event data) and
  **real, verified external links where they add something ESPN's API
  doesn't give directly** - `thesportsmaps.com/nfl` for the NFL regional-
  window problem, and each league's `OUT_OF_MARKET_AUDIO` list (Westwood
  One + iHeartRadio for NFL, MLB Audio + app for MLB, TuneIn for NHL).
  Every one of these was fetched and checked before being wired in, not
  guessed from memory - do the same for any new link: a wrong URL in a
  tool like this is worse than no link at all. A claimed-free option
  needs the SAME check - TuneIn is free for every NHL game but paid-only
  for out-of-market NFL games, which is exactly why NFL's list uses
  iHeartRadio instead, not TuneIn.
- **A small, explicitly-partial `KNOWN_AUDIO` table per league**
  (`leagues/nfl.py`, `mlb.py`, `nhl.py`, and per-instance on `NcaaLeague`
  for NCAA), for verified REGIONAL flagships - distinct from
  `OUT_OF_MARKET_AUDIO` above, which is national/blanket. This exists
  because ESPN's own audio data is CONFIRMED incomplete: a real Bears
  game came back with zero audio entries despite WBBM actively carrying
  every Bears game under a standing contract. Only entries checked by
  hand are here (currently: Bears→WBBM, Cubs→WSCR, Blackhawks→WGN,
  Tennessee football→the Vol Network) - this is deliberately not an
  attempt at all 32 NFL + 30 MLB + hundreds of NCAA teams in one pass.
  Expect it to need re-verification over time, not just extension - the
  Cubs alone changed flagship stations three times in the last decade,
  and a station carrying one team doesn't imply anything about another
  (WGN lost the Cubs but currently holds the Blackhawks).

## Ideas not built yet

Roughly in order of "someone will probably ask for this next":

- **Push/text/calendar reminders** - an `.ics` export per followed team
  would be the simplest version (no new infra, works with any calendar
  app); a "text me an hour before kickoff" mode would need a scheduler
  and a notification channel, a much bigger addition.
- **A real local-market answer for NFL FOX/CBS Sunday windows**, beyond
  the current pointer to thesportsmaps.com. Fully solving this
  programmatically is still blocked by 506sports-style maps refusing
  automated requests - if a non-blocked source ever turns up, this is a
  contained change to `leagues/nfl.py`'s `broadcast_note()`.
- **Expanding `KNOWN_AUDIO`** to more teams than the four verified so
  far, per league/school, each one individually checked - not a bulk
  guess. `leagues/nfl.py`'s comment on the iHeartRadio find (a page
  listing stations for all 32 NFL teams) is a plausible starting point
  for NFL specifically, still needing each entry spot-checked before
  trusting it.
- **Cross-process caching for the NCAA team/conference lists**, if
  latency ever matters (following a big conference means one HTTP call
  per member team plus one for the roster itself). Needs a TTL - see
  "Why nothing is ever cached as an id" above for the constraint any such
  cache has to respect.
- **NBA, WNBA, MLS/soccer, golf, tennis** - see "Adding a pro league"
  above; each is a small, well-understood addition given the existing
  shape. Individual (non-team) sports like golf/tennis would need a
  genuinely different model (players/events, not team schedules) and
  don't fit `resolve.py`'s Team abstraction as-is.
- **A "did my team's game get flexed/rescheduled" diff mode** - compare
  today's fetch against a saved previous one. Would need the caching
  question above settled first.
