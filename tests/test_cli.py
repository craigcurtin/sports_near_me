import pytest

from sports_near_me.cli import _resolve_explicit_teams
from sports_near_me.leagues import nfl


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
