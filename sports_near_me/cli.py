import argparse
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .cli_common import add_shared_flags, configure_logging, logger, resolve_settings
from .espn import audio_note, fetch_schedule, game_for_week, games_within, next_game
from .fetch import DataSourceError
from .leagues import LEAGUES


def _report_data_source_error(e: DataSourceError) -> None:
    """The single place a DataSourceError becomes user-facing output -
    every call site below routes through this so the breadcrumb (URL,
    what was being attempted, where to look - see fetch.py) always
    reaches the terminal, not just the log file. Full traceback still
    goes to the log via logger.exception, for the rarer case where the
    breadcrumb itself isn't enough."""
    logger.exception("Data source failure")
    print(f"error: {e}", file=sys.stderr)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sports-game",
        description="When do your followed teams play next, and can you watch them?",
    )
    add_shared_flags(parser)
    subparsers = parser.add_subparsers(dest="sport", metavar="{" + ",".join(LEAGUES) + "}")
    for name in LEAGUES:
        sub = subparsers.add_parser(name, help=name.upper())
        sub.add_argument("team", nargs="*", default=None,
                          help="A specific team, or several - as 'tennessee,wisconsin', "
                               "'tennessee, wisconsin' (space after the comma is fine "
                               "unquoted too), or plain separate words. Overrides your "
                               "config's follow list for this run.")
        add_shared_flags(sub)
    return parser


def _resolve_explicit_teams(league, raw: str) -> list:
    """Resolves a command-line team argument, which may be a single name
    or a comma-separated list ("tennessee,wisconsin") - each name goes
    through the exact same league.resolve_team() a single-team lookup
    uses, so ambiguity/not-found errors are exactly as specific either
    way. Deduplicated by resolved id (same reasoning as
    _followed_teams_for()'s dedup), in case two different spellings in
    the list point at the same team."""
    teams_by_id = {}
    for name in (n.strip() for n in raw.split(",")):
        if not name:
            continue
        team = league.resolve_team(name)
        teams_by_id[team.id] = team
    return list(teams_by_id.values())


def _followed_teams_for(sport: str, follow_cfg: dict) -> list:
    """Resolves one sport's follow config (explicit teams + whole
    conferences) into a deduplicated list of resolve.Team objects. A team
    reachable both directly and via a followed conference is only shown
    once."""
    league = LEAGUES[sport]
    cfg = follow_cfg.get(sport) or {}
    teams_by_id = {}

    for name in cfg.get("teams", []):
        team = league.resolve_team(name)
        teams_by_id[team.id] = team

    for conf_name in cfg.get("conferences", []):
        if not hasattr(league, "resolve_conf"):
            logger.warning(f"{sport} has no conference support - skipping '{conf_name}'")
            continue
        conference = league.resolve_conf(conf_name)
        for member in league.conf_members(conference.id):
            teams_by_id[member.id] = member

    return list(teams_by_id.values())


def _display_tz(settings):
    # Default to this machine's own local timezone - most people run this
    # from wherever they actually are, and forcing everyone to convert
    # from UTC by hand is worse than the rare case where the machine's
    # clock isn't where the viewer is (that's what --tz/config tz are
    # for). The one thing that's never optional is showing WHICH zone was
    # used - see %Z in _format_game - so nothing here is hidden, even
    # though it's not always explicit.
    return ZoneInfo(settings["tz"]) if settings["tz"] else datetime.now().astimezone().tzinfo


def _format_game(league, team, game, display_tz) -> None:
    local_kickoff = game.kickoff_utc.astimezone(display_tz)
    opponent = game.opponent_name_for(team.id)
    vs_or_at = "vs." if game.is_home_for(team.id) else "at"
    week_label = f"Week {game.week}" if game.week else "Game"

    print(f"{week_label}: {team.display_name} {vs_or_at} {opponent}")
    print(f"Kickoff: {local_kickoff.strftime('%A, %B %d, %Y  %I:%M %p %Z')}")
    print(f"Venue:   {game.venue_name} ({game.venue_city}, {game.venue_state})")
    print(f"TV:      {league.broadcast_note(game)}")

    audio = audio_note(game)
    print(f"Audio:   {audio}")

    # A hand-verified regional flagship (see leagues/nfl.py's/mlb.py's/
    # nhl.py's KNOWN_AUDIO) is worth printing whether or not ESPN itself
    # reported anything - this is exactly the case that motivated it:
    # ESPN's feed missing a real, currently-active broadcast (confirmed
    # for a real Bears game against WBBM's own standing contract).
    known_audio_fn = getattr(league, "known_audio", None)
    known = known_audio_fn(team.id) if known_audio_fn else None
    if known:
        station, url = known
        print(f"         Verified regional flagship: {station} - {url}")

    # A league can optionally list its own standing national audio
    # options (Westwood One + iHeartRadio for NFL, MLB Audio + app for
    # MLB, TuneIn for NHL) - each entry individually verified real and,
    # where claimed free, actually free (SiriusXM/TuneIn Premium were
    # checked for NFL and deliberately left out - paid-only there, unlike
    # NHL). NOT gated on whether ESPN reported an audio entry for this
    # specific game - these are blanket "every game, every team" services
    # that apply regardless of ESPN's own (confirmed incomplete) per-game
    # audio data, unlike a regional flagship which is one specific team's
    # own broadcast.
    out_of_market = getattr(league, "OUT_OF_MARKET_AUDIO", [])
    if out_of_market:
        print("         Out-of-market listeners:")
        for label, url in out_of_market:
            print(f"           {label}: {url}")

    if game.link:
        print(f"More at: {game.link}")


def _print_team(league, team, settings) -> None:
    try:
        games = fetch_schedule(league.SPORT, league.LEAGUE, team.id)
    except DataSourceError as e:
        _report_data_source_error(e)
        return
    except Exception:
        # Not a recognized data-source failure - an actual bug somewhere
        # in this codebase, not ESPN's API changing shape. Still surfaced
        # loudly (full traceback to the log) rather than silently eaten,
        # but without pretending to know where to look the way a
        # DataSourceError's breadcrumb does.
        logger.exception(f"Unexpected failure fetching schedule for {team.display_name}")
        print(f"error: unexpected failure fetching {team.display_name}'s schedule - "
              f"see the log for the full traceback; this doesn't look like a known "
              f"ESPN data-source issue.", file=sys.stderr)
        return
    logger.info(f"Fetched {len(games)} game(s) for {team.display_name}")

    display_tz = _display_tz(settings)

    if settings["week"] is not None:
        selected = [g for g in [game_for_week(games, settings["week"])] if g]
        scope = f"week {settings['week']}"
    elif settings["range"] is not None:
        selected = games_within(games, settings["range"], display_tz)
        scope = f"the next {settings['range']} day(s)"
    else:
        selected = [g for g in [next_game(games)] if g]
        scope = "an upcoming game"

    if not selected:
        print(f"{team.display_name}: no game found for {scope}.")
        return

    for i, game in enumerate(selected):
        if len(selected) > 1 and i > 0:
            print()
        _format_game(league, team, game, display_tz)


def run(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        settings = resolve_settings(args)
    except (FileNotFoundError, ImportError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    configure_logging(settings)
    if settings.get("_config_created"):
        # Always visible, even under --silent - creating a file on
        # someone's machine is worth surfacing every time, not just as a
        # routine diagnostic. Explicit CLI args (a sport/team given
        # directly) still completely bypass this file's follow list for
        # the current run - it only supplies defaults for the
        # no-team/no-sport "show everything I follow" invocations.
        print(f"No config file found - created one with a starter team "
              f"list at {settings['_config_path']}. Edit that file (or "
              f"pass --config to use a different one) to set your own "
              f"teams.", file=sys.stderr)
    elif settings["_config_path"]:
        logger.info(f"Loaded config from {settings['_config_path']}")

    sports_to_run = [args.sport] if args.sport else list(settings["_follow"].keys())
    if not sports_to_run:
        print("error: no sport given, and no 'follow:' section in your config file. "
              "Pass a sport (e.g. 'sports-game nfl bears') or set up "
              "~/.sports_near_me.yaml - see config.example.yaml.", file=sys.stderr)
        return 1

    jobs = []  # list of (sport, Team)
    for sport in sports_to_run:
        if sport not in LEAGUES:
            print(f"error: unknown sport '{sport}' in config's follow list - skipping.", file=sys.stderr)
            continue
        league = LEAGUES[sport]

        explicit_team = args.sport and getattr(args, "team", None)
        if explicit_team:
            # "team" collects every shell token after the sport (nargs="*"),
            # not just one - joined with "," before splitting again in
            # _resolve_explicit_teams() so "cubs, brewers" (space after the
            # comma, unquoted) works exactly like "cubs,brewers" or a
            # properly quoted "cubs, brewers": the shell splits the
            # unquoted form into two tokens ("cubs," and "brewers"), and
            # rejoining with "," turns that back into one team list
            # instead of an argparse "unrecognized arguments" error.
            raw = ",".join(args.team)
            try:
                teams = _resolve_explicit_teams(league, raw)
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                return 1
            except DataSourceError as e:
                _report_data_source_error(e)
                return 1
            jobs.extend((sport, t) for t in teams)
            continue

        try:
            teams = _followed_teams_for(sport, settings["_follow"])
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        except DataSourceError as e:
            _report_data_source_error(e)
            return 1
        if not teams:
            print(f"error: no team given for {sport}, and nothing under follow.{sport} in your "
                  f"config. Pass a team (e.g. 'sports-game {sport} bears') or add one to "
                  f"follow.{sport}.teams / follow.{sport}.conferences.", file=sys.stderr)
            continue
        jobs.extend((sport, t) for t in teams)

    if not jobs:
        return 1

    # Schedules aren't static - weather, doubleheaders, and other
    # rescheduling can add/move/cancel a game after this report is
    # generated. Printing when the data was actually fetched (not when
    # someone happens to be reading it later) is what makes that
    # staleness visible instead of silent.
    display_tz = _display_tz(settings)
    fetched_at = datetime.now(timezone.utc).astimezone(display_tz)
    print(f"As of: {fetched_at.strftime('%A, %B %d, %Y  %I:%M %p %Z')} - schedules can change after this.")
    print()

    show_headers = len(jobs) > 1
    for i, (sport, team) in enumerate(jobs):
        if show_headers:
            if i > 0:
                print()
            print(f"=== {sport.upper()}: {team.display_name} ===")
        _print_team(LEAGUES[sport], team, settings)

    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
