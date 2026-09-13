from sports_near_me.espn import Broadcast, Game
from sports_near_me.leagues import nhl


def _game(broadcasts):
    return Game(
        event_id="1", name="Test", kickoff_utc=None, week=None,
        home_id="CHI", away_id="VGK", home_abbr="CHI", away_abbr="VGK",
        home_name="Chicago Blackhawks", away_name="Vegas Golden Knights",
        venue_name="", venue_city="", venue_state="", broadcasts=broadcasts,
    )


def test_resolve_by_nickname():
    assert nhl.resolve_team("blackhawks").id == "CHI"


def test_broadcast_note_national():
    game = _game([Broadcast(network="ESPN", medium="TV", market_type="National")])
    assert "national broadcast" in nhl.broadcast_note(game).lower()


def test_broadcast_note_empty_is_hedged_not_flat():
    # Regional-only NHL games commonly come back with an empty broadcasts
    # list in ESPN's feed - that should read as "check locally," not
    # "nothing airs."
    game = _game([])
    note = nhl.broadcast_note(game).lower()
    assert "regional" in note
    assert "check your team" in note


def test_known_audio_verified_team():
    station, url = nhl.known_audio("CHI")
    assert "WGN" in station
    assert url.startswith("https://")


def test_known_audio_unverified_team_returns_none():
    assert nhl.known_audio("VGK") is None
