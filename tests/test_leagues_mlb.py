from sports_near_me.espn import Broadcast, Game
from sports_near_me.leagues import mlb


def _game(broadcasts):
    return Game(
        event_id="1", name="Test", kickoff_utc=None, week=None,
        home_id="16", away_id="23", home_abbr="CHC", away_abbr="WSH",
        home_name="Chicago Cubs", away_name="Washington Nationals",
        venue_name="", venue_city="", venue_state="", broadcasts=broadcasts,
    )


def test_resolve_by_nickname():
    assert mlb.resolve_team("cubs").id == "CHC"


def test_broadcast_note_lists_home_away_national():
    game = _game([
        Broadcast(network="MLB.TV", medium="Streaming", market_type="National"),
        Broadcast(network="Marquee Sports Net", medium="TV", market_type="Home"),
        Broadcast(network="Nationals.TV", medium="Streaming", market_type="Away"),
    ])
    note = mlb.broadcast_note(game)
    assert "Marquee Sports Net" in note
    assert "Nationals.TV" in note
    assert "MLB.TV" in note
    assert "blacks out" in note  # the blackout caveat is appended when MLB.TV is present


def test_broadcast_note_excludes_radio():
    game = _game([
        Broadcast(network="Marquee Sports Net", medium="TV", market_type="Home"),
        Broadcast(network="ERADM", medium="Radio", market_type="National"),
    ])
    note = mlb.broadcast_note(game)
    assert "ERADM" not in note
    assert "Marquee Sports Net" in note


def test_broadcast_note_no_tv_or_streaming():
    game = _game([Broadcast(network="ERADM", medium="Radio", market_type="National")])
    assert "not yet announced" in mlb.broadcast_note(game).lower()


def test_known_audio_verified_team():
    station, url = mlb.known_audio("CHC")
    assert "670 The Score" in station
    assert url.startswith("https://")


def test_known_audio_second_verified_team():
    station, url = mlb.known_audio("CWS")
    assert "ESPN 1000" in station
    assert url.startswith("https://")


def test_known_audio_unverified_team_returns_none():
    assert mlb.known_audio("NYY") is None
