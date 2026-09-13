from datetime import datetime, timedelta, timezone

from sports_near_me.espn import Broadcast, Game, _has_upcoming_event, game_for_week, next_game, radio_note


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


def test_radio_note_none_listed():
    g = _game("1", 1, "2026-09-13T17:00:00", broadcasts=[Broadcast("FOX", "TV", "National")])
    assert radio_note(g) == "No radio broadcast listed."


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


def test_radio_note_lists_entries():
    g = _game("1", 1, "2026-09-13T17:00:00", broadcasts=[
        Broadcast("WGN Radio", "Radio", "Home"),
        Broadcast("ESPN Radio", "Radio", "National"),
    ])
    note = radio_note(g)
    assert "WGN Radio" in note
    assert "ESPN Radio" in note
