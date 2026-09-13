from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from sports_near_me.espn import (
    Broadcast, Game, _has_upcoming_event, _parse_events, audio_note,
    fetch_schedule, game_for_week, games_within, next_game,
)
from sports_near_me.fetch import DataSourceError


def _raw_event(iso_date, completed=False):
    return {
        "date": iso_date,
        "competitions": [{"status": {"type": {"completed": completed}}}],
    }


def _game(event_id, week, kickoff_iso, broadcasts=(), completed=False):
    return Game(
        event_id=event_id, name="Test", kickoff_utc=datetime.fromisoformat(kickoff_iso).replace(tzinfo=timezone.utc),
        week=week, home_id="A", away_id="B", home_abbr="A", away_abbr="B",
        home_name="Home Team", away_name="Away Team",
        venue_name="", venue_city="", venue_state="", broadcasts=list(broadcasts), completed=completed,
    )


def test_next_game_skips_completed_and_past():
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    games = [
        _game("1", 1, "2026-09-01T17:00:00", completed=True),
        _game("2", 2, "2026-09-13T17:00:00"),
        _game("3", 3, "2026-09-20T17:00:00"),
    ]
    assert next_game(games, now=now).event_id == "2"


def test_game_for_week():
    games = [_game("1", 1, "2026-09-01T17:00:00"), _game("2", 2, "2026-09-13T17:00:00")]
    assert game_for_week(games, 2).event_id == "2"
    assert game_for_week(games, 5) is None


def test_is_home_and_opponent():
    g = _game("1", 1, "2026-09-13T17:00:00")
    assert g.is_home_for("A") is True
    assert g.is_home_for("B") is False
    assert g.opponent_name_for("A") == "Away Team"
    assert g.opponent_name_for("B") == "Home Team"


def test_is_home_matches_numeric_id_or_abbreviation():
    # Regression: MLB/NFL/NHL resolve teams to their abbreviation (e.g.
    # "CHC"), but ESPN's competitor id on each game is numeric (e.g. "16").
    # is_home_for()/opponent_name_for() must match either form, or a
    # league using abbreviations would never recognize its own team as
    # home or away - this is exactly the bug that made a real Cubs game
    # print as "Chicago Cubs at Chicago Cubs" before the fix.
    g = Game(
        event_id="1", name="Test", kickoff_utc=None, week=None,
        home_id="16", away_id="23", home_abbr="CHC", away_abbr="WSH",
        home_name="Chicago Cubs", away_name="Washington Nationals",
        venue_name="", venue_city="", venue_state="",
    )
    assert g.is_home_for("CHC") is True   # abbreviation form (MLB/NFL/NHL)
    assert g.is_home_for("16") is True    # numeric form (NCAA)
    assert g.is_home_for("WSH") is False
    assert g.opponent_name_for("CHC") == "Washington Nationals"
    assert g.opponent_name_for("WSH") == "Chicago Cubs"


def test_audio_note_none_listed():
    # Deliberately hedged, not a flat "no broadcast" - ESPN's feed is
    # confirmed to miss real, currently-active flagship stations.
    g = _game("1", 1, "2026-09-13T17:00:00", broadcasts=[Broadcast("FOX", "TV", "National")])
    note = audio_note(g)
    assert "None listed in ESPN's data" in note
    assert "known gap" in note


def test_has_upcoming_event_true_for_future_uncompleted_game():
    future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%MZ")
    assert _has_upcoming_event({"events": [_raw_event(future)]}) is True


def test_has_upcoming_event_false_when_all_past():
    # Regression: this is the exact shape of the bug where an entire
    # already-finished season (all games in the past) was almost trusted
    # as "the current schedule" just because the events list was non-empty.
    past = (datetime.now(timezone.utc) - timedelta(days=200)).strftime("%Y-%m-%dT%H:%MZ")
    assert _has_upcoming_event({"events": [_raw_event(past)]}) is False


def test_has_upcoming_event_false_when_future_but_marked_completed():
    future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%MZ")
    assert _has_upcoming_event({"events": [_raw_event(future, completed=True)]}) is False


def test_has_upcoming_event_false_for_empty():
    assert _has_upcoming_event({"events": []}) is False
    assert _has_upcoming_event({}) is False


def test_audio_note_lists_entries():
    g = _game("1", 1, "2026-09-13T17:00:00", broadcasts=[
        Broadcast("WGN Radio", "Radio", "Home"),
        Broadcast("ESPN Radio", "Radio", "National"),
    ])
    note = audio_note(g)
    assert "WGN Radio" in note
    assert "ESPN Radio" in note


def test_games_within_one_day_is_today_only():
    now = datetime(2026, 9, 13, 15, 0, tzinfo=timezone.utc)
    games = [
        _game("1", None, "2026-09-12T23:00:00"),  # yesterday
        _game("2", None, "2026-09-13T02:00:00"),  # earlier today - included even though past
        _game("3", None, "2026-09-13T23:00:00"),  # later today
        _game("4", None, "2026-09-14T02:00:00"),  # tomorrow
    ]
    result = games_within(games, days=1, tz=timezone.utc, now=now)
    assert [g.event_id for g in result] == ["2", "3"]


def test_games_within_seven_days_is_this_week():
    now = datetime(2026, 9, 13, 15, 0, tzinfo=timezone.utc)
    games = [
        _game("1", None, "2026-09-12T23:00:00"),  # yesterday - excluded
        _game("2", None, "2026-09-13T02:00:00"),  # today
        _game("3", None, "2026-09-19T23:00:00"),  # day 7 (today + 6) - included
        _game("4", None, "2026-09-20T02:00:00"),  # day 8 - excluded
    ]
    result = games_within(games, days=7, tz=timezone.utc, now=now)
    assert [g.event_id for g in result] == ["2", "3"]


def test_games_within_respects_display_timezone():
    # 2026-09-13T02:00 UTC is still 2026-09-12 evening in US/Eastern -
    # "today" has to be computed in the DISPLAY timezone, not UTC, or a
    # late-UTC/early-local game gets attributed to the wrong calendar day.
    now = datetime(2026, 9, 13, 4, 0, tzinfo=timezone.utc)  # midnight Eastern
    games = [_game("1", None, "2026-09-13T02:00:00")]  # 10pm Eastern on the 12th
    eastern = ZoneInfo("America/New_York")
    assert games_within(games, days=1, tz=eastern, now=now) == []
    assert games_within(games, days=1, tz=timezone.utc, now=now) != []


def test_games_within_sorted_by_kickoff():
    now = datetime(2026, 9, 13, 0, 0, tzinfo=timezone.utc)
    games = [
        _game("later", None, "2026-09-14T20:00:00"),
        _game("earlier", None, "2026-09-13T10:00:00"),
    ]
    result = games_within(games, days=3, tz=timezone.utc, now=now)
    assert [g.event_id for g in result] == ["earlier", "later"]


def _valid_event(event_id="1"):
    return {
        "id": event_id, "name": "Test", "date": "2026-09-13T17:00Z",
        "week": {"number": 1}, "links": [],
        "competitions": [{
            "venue": {"fullName": "Test Stadium", "address": {"city": "Test City", "state": "TS"}},
            "competitors": [
                {"homeAway": "home", "team": {"id": "1", "abbreviation": "HOM", "displayName": "Home Team"}},
                {"homeAway": "away", "team": {"id": "2", "abbreviation": "AWY", "displayName": "Away Team"}},
            ],
            "broadcasts": [],
            "status": {"type": {"completed": False}},
        }],
    }


def test_parse_events_happy_path():
    data = {"events": [_valid_event()]}
    games = _parse_events(data, "https://example.test/schedule", "testing")
    assert len(games) == 1
    assert games[0].home_name == "Home Team"


def test_parse_events_missing_field_raises_data_source_error_with_breadcrumb():
    # "competitions" missing entirely - exactly what an ESPN-side rename
    # of that field would look like.
    bad_event = _valid_event()
    del bad_event["competitions"]
    data = {"events": [bad_event]}
    with pytest.raises(DataSourceError) as exc_info:
        _parse_events(data, "https://example.test/schedule", "testing schedule")
    message = str(exc_info.value)
    assert "https://example.test/schedule" in message
    assert "testing schedule" in message
    assert "KeyError" in message


def test_fetch_schedule_propagates_data_source_error_with_breadcrumb():
    # fetch_json itself is mocked here, not urllib - this test is about
    # fetch_schedule()'s own context string reaching the final error, not
    # re-testing fetch_json's HTTP-layer wrapping (see test_fetch.py).
    with patch("sports_near_me.espn.fetch_json", return_value={"events": "not-a-list-of-dicts-but-a-string"}):
        with pytest.raises(DataSourceError) as exc_info:
            fetch_schedule("football", "nfl", "CHI")
    message = str(exc_info.value)
    assert "football/nfl" in message
    assert "team_id=CHI" in message
