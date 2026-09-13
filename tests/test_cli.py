import pytest

from sports_near_me.cli import _resolve_explicit_teams, build_arg_parser
from sports_near_me.leagues import mlb, nfl


def _parsed_team_arg(argv):
    """What build_arg_parser() actually hands run() for the 'team'
    positional, given a real argv list - this is the layer that decides
    whether an unquoted 'cubs, brewers' (the shell splits that into two
    argv tokens: 'cubs,' and 'brewers') gets rejected outright or
    survives to reach _resolve_explicit_teams() at all."""
    args = build_arg_parser().parse_args(argv)
    return args.team


def test_team_arg_single_token():
    assert _parsed_team_arg(["mlb", "cubs"]) == ["cubs"]


def test_team_arg_no_team_given_is_empty_list():
    assert _parsed_team_arg(["mlb"]) == []


def test_team_arg_quoted_comma_list_is_one_token():
    # Shell quoting means "cubs,brewers" arrives as ONE argv entry.
    assert _parsed_team_arg(["mlb", "cubs,brewers"]) == ["cubs,brewers"]


def test_team_arg_unquoted_space_after_comma_is_two_tokens():
    # This is the actual shell-splitting case a friend hits typing
    # `sports-game mlb cubs, brewers` with no quotes - argparse must
    # collect both tokens (nargs="*") rather than rejecting the second
    # one as an unrecognized argument, so run() can rejoin them with ","
    # before handing off to _resolve_explicit_teams().
    assert _parsed_team_arg(["mlb", "cubs,", "brewers"]) == ["cubs,", "brewers"]
    # And joining is exactly what turns that back into a valid team list:
    rejoined = ",".join(_parsed_team_arg(["mlb", "cubs,", "brewers"]))
    teams = _resolve_explicit_teams(mlb, rejoined)
    assert [t.id for t in teams] == ["CHC", "MIL"]


def test_team_arg_bare_words_no_comma_is_two_tokens():
    assert _parsed_team_arg(["mlb", "cubs", "brewers"]) == ["cubs", "brewers"]


def test_resolve_explicit_teams_single():
    teams = _resolve_explicit_teams(nfl, "bears")
    assert [t.id for t in teams] == ["CHI"]


def test_resolve_explicit_teams_comma_separated():
    teams = _resolve_explicit_teams(nfl, "bears,packers")
    assert [t.id for t in teams] == ["CHI", "GB"]


def test_resolve_explicit_teams_tolerates_whitespace():
    teams = _resolve_explicit_teams(nfl, " bears , packers ")
    assert [t.id for t in teams] == ["CHI", "GB"]


def test_resolve_explicit_teams_ignores_empty_segments():
    # A trailing/double comma ("bears,,packers" or "bears,") shouldn't
    # try to resolve an empty string as a team name.
    teams = _resolve_explicit_teams(nfl, "bears,,packers,")
    assert [t.id for t in teams] == ["CHI", "GB"]


def test_resolve_explicit_teams_dedupes_by_resolved_id():
    # "bears" and "chicago bears" both resolve to CHI - listing both
    # shouldn't produce the same team twice.
    teams = _resolve_explicit_teams(nfl, "bears,chicago bears")
    assert [t.id for t in teams] == ["CHI"]


def test_resolve_explicit_teams_raises_on_one_bad_name():
    with pytest.raises(ValueError, match="isn't a team I recognize"):
        _resolve_explicit_teams(nfl, "bears,not-a-real-team")


def test_resolve_explicit_teams_raises_on_ambiguous_name():
    with pytest.raises(ValueError, match="matches more than one team"):
        _resolve_explicit_teams(nfl, "bears,new york")
