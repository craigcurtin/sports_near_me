"""
Generic ESPN site-API schedule fetch, shared by every league.

Two ESPN quirks this module works around, both confirmed by hand before
writing the fix (see the project's session history, not repeated here):

1. Team identity for the URL path is the numeric competitor id for NCAA
   (abbreviation routing collides there - .../teams/osu/schedule silently
   answers with a small branch-campus team, not Ohio State) but the plain
   abbreviation for NFL/MLB/NHL (those route correctly, no extra lookup
   needed). Game.home_id/away_id store BOTH forms per team precisely
   because of that split - is_home_for()/opponent_name_for() have to match
   against whichever form the caller's Team.id happens to be, or a league
   using abbreviations (MLB) would never match its own numeric competitor
   ids and every home/away call would silently return the wrong team.
2. The schedule endpoint's default "season" is inconsistent per sport, AND
   college sports don't agree whether "season N" means the year it starts
   or the year it ends (confirmed: NCAA men's basketball's season=2026 is
   the already-finished 2025-26 season, not 2026-27). fetch_schedule()
   retries with explicit season guesses when the default has no upcoming
   game, but only trusts a guess that itself has an upcoming game - see
   _has_upcoming_event()'s docstring for why that guard exists.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from .fetch import fetch_json, parse_error

SCHEDULE_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_id}/schedule"


@dataclass(frozen=True)
class Broadcast:
    network: str
    medium: str        # "TV" or "Streaming"
    market_type: str   # "National", "Home", "Away" - as ESPN reports it


@dataclass(frozen=True)
class Game:
    event_id: str
    name: str
    kickoff_utc: datetime
    week: Optional[int]
    home_id: str
    away_id: str
    home_abbr: str
    away_abbr: str
    home_name: str
    away_name: str
    venue_name: str
    venue_city: str
    venue_state: str
    link: Optional[str] = None
    broadcasts: list = field(default_factory=list)
    completed: bool = False

    def is_home_for(self, team_id: str) -> bool:
        return team_id in (self.home_id, self.home_abbr)

    def opponent_name_for(self, team_id: str) -> str:
        return self.away_name if self.is_home_for(team_id) else self.home_name


def _has_upcoming_event(data: dict) -> bool:
    now = datetime.now(timezone.utc)
    for event in data.get("events", []):
        completed = event["competitions"][0].get("status", {}).get("type", {}).get("completed", False)
        if completed:
            continue
        kickoff = datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        if kickoff >= now:
            return True
    return False


def _parse_events(data: dict, url: str, context: str) -> list:
    """Turns one already-fetched schedule response into Game objects.
    Split out from fetch_schedule() so a shape-mismatch here is both
    independently testable (no network mocking needed) and reported with
    a breadcrumb naming the URL and context, via parse_error() - a bare
    KeyError/IndexError/TypeError three frames into a dict-walk is exactly
    the kind of failure this project wants to never leave unexplained."""
    try:
        games = []
        for event in data.get("events", []):
            competition = event["competitions"][0]
            venue = competition.get("venue", {})
            address = venue.get("address", {})

            home_id = home_abbr = home_name = away_id = away_abbr = away_name = None
            for competitor in competition.get("competitors", []):
                team = competitor["team"]
                name = team.get("displayName") or team.get("name", "")
                abbr = team.get("abbreviation", "")
                if competitor["homeAway"] == "home":
                    home_id, home_abbr, home_name = team["id"], abbr, name
                else:
                    away_id, away_abbr, away_name = team["id"], abbr, name

            broadcasts = [
                Broadcast(
                    network=b["media"]["shortName"],
                    medium=b["type"]["shortName"],
                    # Unlike MLB, which always reports Home/Away/National,
                    # some broadcast entries carry no "market" at all - seen
                    # live on an NCAA soccer conference-network stream
                    # (B1G+). Absent, not malformed: NCAA's own
                    # broadcast_note() doesn't read market_type anyway (see
                    # leagues/_ncaa.py), so this is safe to leave blank
                    # rather than treat as a parse failure.
                    market_type=b.get("market", {}).get("type", ""),
                )
                for b in competition.get("broadcasts", [])
            ]

            link = None
            for entry in event.get("links", []):
                rel = entry.get("rel", [])
                if "summary" in rel and "desktop" in rel:
                    link = entry.get("href")
                    break

            games.append(Game(
                event_id=event["id"],
                name=event["name"],
                kickoff_utc=datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc),
                week=event.get("week", {}).get("number"),
                home_id=home_id,
                away_id=away_id,
                home_abbr=home_abbr,
                away_abbr=away_abbr,
                home_name=home_name,
                away_name=away_name,
                venue_name=venue.get("fullName", ""),
                venue_city=address.get("city", ""),
                venue_state=address.get("state", ""),
                link=link,
                broadcasts=broadcasts,
                completed=competition.get("status", {}).get("type", {}).get("completed", False),
            ))
        return games
    except (KeyError, IndexError, TypeError) as e:
        raise parse_error(context, url, e) from e


def fetch_schedule(sport: str, league: str, team_id: str) -> list:
    """One season's worth of games for the given team id, in the order
    ESPN returns them (chronological in practice).

    If the default response has no upcoming game, retries with an explicit
    season - confirmed necessary for some sports (NCAA men's basketball)
    and not others. Critically, a retried season is only trusted if IT ALSO
    has an upcoming game: college sports don't agree on whether "season N"
    means the year it starts or the year it ends, and blindly trusting any
    non-empty retry once produced a fully-completed PAST season presented
    as if it were current (Duke men's basketball's already-finished
    2025-26 season, under season=2026) - worse than the honest empty
    result it was "fixing." If neither guess turns up anything upcoming,
    that's reported as-is: the schedule genuinely isn't published yet.

    Any failure - unreachable URL, a non-2xx response, invalid JSON, or
    JSON that doesn't have the shape expected below - raises
    fetch.DataSourceError with the URL and what was being attempted, so
    the failure is never a bare traceback with no indication of where to
    look (see fetch.py's docstring)."""
    context = f"fetching {sport}/{league} schedule for team_id={team_id}"
    url = SCHEDULE_URL.format(sport=sport, league=league, team_id=team_id)
    data = fetch_json(url, context)

    try:
        needs_retry = not _has_upcoming_event(data)
    except (KeyError, IndexError, TypeError) as e:
        raise parse_error(context, url, e) from e

    if needs_retry:
        today = date.today()
        for season in (today.year, today.year + 1):
            season_url = f"{url}?season={season}"
            candidate = fetch_json(season_url, f"{context} (season={season} retry)")
            try:
                found = _has_upcoming_event(candidate)
            except (KeyError, IndexError, TypeError) as e:
                raise parse_error(f"{context} (season={season} retry)", season_url, e) from e
            if found:
                data = candidate
                url = season_url
                break

    return _parse_events(data, url, context)


def next_game(games: list, now: Optional[datetime] = None) -> Optional[Game]:
    now = now or datetime.now(timezone.utc)
    upcoming = [g for g in games if g.kickoff_utc >= now and not g.completed]
    return min(upcoming, key=lambda g: g.kickoff_utc) if upcoming else None


def game_for_week(games: list, week: int) -> Optional[Game]:
    matches = [g for g in games if g.week == week]
    return matches[0] if matches else None


def games_within(games: list, days: int, tz, now: Optional[datetime] = None) -> list:
    """Every game from today through (days - 1) days from now - days=1 is
    "today only," days=7 is "this week" - by calendar date IN THE GIVEN
    DISPLAY TIMEZONE. "Today" is a calendar concept, so this has to use
    whatever timezone the report is being shown in (which defaults to UTC,
    per the "never guess the viewer's timezone" rule in cli.py - pass an
    explicit tz here for a real local-calendar window). Includes games
    already finished earlier today, not just upcoming ones - this is
    "what's on this window," not "what's next.\""""
    now = now or datetime.now(timezone.utc)
    start = now.astimezone(tz).date()
    end = start + timedelta(days=days - 1)
    return sorted(
        (g for g in games if start <= g.kickoff_utc.astimezone(tz).date() <= end),
        key=lambda g: g.kickoff_utc,
    )


_MARKET_LABELS = {"National": "National", "Home": "Home", "Away": "Away"}


def audio_note(game: Game) -> str:
    """Generic across every league. Called "Audio" rather than "Radio" -
    ESPN's own medium type here is literally "Radio," but what it actually
    lists is mostly consumed as internet audio today (team flagship
    stations simulcast on their own apps/TuneIn as often as a physical
    AM/FM dial), so "Radio" undersells it. Audio doesn't have NFL's
    regional-map ambiguity problem - it's just "this station/stream
    carries it" - so one shared formatter (grouped the same National/
    Home/Away way MLB's TV data is) covers every sport rather than needing
    a per-league implementation. Home/Away entries are a specific
    market's real regional broadcast (useful if you're in that market);
    a National entry is the one a remote/out-of-market listener actually
    wants - both are worth keeping, not just the national one.

    The empty case is deliberately hedged, not a flat "no broadcast":
    confirmed by hand that ESPN's feed misses real, currently-active
    flagship stations (WBBM Newsradio has carried every Bears game since
    2000, under a standing multi-year extension - a Bears game with no
    audio entry here is ESPN's gap, not evidence WBBM isn't carrying it).
    Every team in every league covered here has a local flagship
    station/stream ESPN simply doesn't always report - assume one exists
    regionally rather than reading a blank line as "nothing airs.\""""
    audio = [b for b in game.broadcasts if b.medium == "Radio"]
    if not audio:
        return ("None listed in ESPN's data - that's a known gap, not evidence there isn't one. "
                "Your team's local flagship station/stream almost certainly still carries this "
                "regionally; check the team's own site/app if you need it.")
    return " | ".join(f"{_MARKET_LABELS.get(b.market_type, b.market_type)}: {b.network}" for b in audio)
