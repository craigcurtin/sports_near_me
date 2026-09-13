import pytest

from sports_near_me.espn import Broadcast, Game
from sports_near_me.leagues import nfl


def _game(network, medium="TV", market_type="National"):
    return Game(
        event_id="1", name="Test", kickoff_utc=None, week=1,
        home_id="CAR", away_id="CHI", home_abbr="CAR", away_abbr="CHI",
        home_name="Carolina Panthers", away_name="Chicago Bears",
        venue_name="", venue_city="", venue_state="",
        broadcasts=[Broadcast(network=network, medium=medium, market_type=market_type)],
    )


def test_resolve_by_nickname():
    assert nfl.resolve_team("bears").id == "CHI"


def test_resolve_ambiguous_city_raises():
    with pytest.raises(ValueError, match="matches more than one team"):
        nfl.resolve_team("new york")


def test_broadcast_note_national():
    assert "national broadcast" in nfl.broadcast_note(_game("NBC")).lower()


def test_broadcast_note_regional():
    assert "regional" in nfl.broadcast_note(_game("FOX")).lower()


def test_broadcast_note_no_broadcast():
    game = Game(
        event_id="1", name="Test", kickoff_utc=None, week=1,
        home_id="CAR", away_id="CHI", home_abbr="CAR", away_abbr="CHI",
        home_name="Carolina Panthers", away_name="Chicago Bears",
        venue_name="", venue_city="", venue_state="", broadcasts=[],
    )
    assert "not yet announced" in nfl.broadcast_note(game).lower()


def test_broadcast_note_skips_radio_only():
    game = _game("ESPN Radio", medium="Radio")
    assert "not yet announced" in nfl.broadcast_note(game).lower()


def test_known_audio_verified_team():
    station, url = nfl.known_audio("CHI")
    assert "WBBM" in station
    assert url.startswith("https://")


def test_known_audio_unverified_team_returns_none():
    assert nfl.known_audio("SF") is None
