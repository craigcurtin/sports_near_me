from sports_near_me.leagues import ncaaf, ncaamb
from sports_near_me.leagues._ncaa import NcaaLeague


def test_known_audio_verified_team():
    station, url = ncaaf.known_audio("2633")  # Tennessee Volunteers football
    assert "Vol Network" in station
    assert url.startswith("https://")


def test_known_audio_unverified_team_returns_none():
    assert ncaaf.known_audio("194") is None  # Ohio State - not in the table


def test_known_audio_is_per_instance_not_shared_across_sports():
    # A school's numeric ESPN id differs per sport (see dynamic_teams.py),
    # so an NcaaLeague built with no known_audio must never see another
    # instance's table - regression against a shared mutable default.
    other = NcaaLeague("basketball", "mens-college-basketball")
    assert other.known_audio("2633") is None
    assert ncaamb.known_audio("2633") is None
