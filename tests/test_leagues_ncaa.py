from sports_near_me.leagues import ncaabsb, ncaaf, ncaamb, ncaawb
from sports_near_me.leagues._ncaa import NcaaLeague


def test_known_audio_verified_team():
    station, url = ncaaf.known_audio("2633")  # Tennessee Volunteers football
    assert "Vol Network" in station
    assert url.startswith("https://")


def test_known_audio_unverified_team_returns_none():
    assert ncaaf.known_audio("194") is None  # Ohio State - not in the table


def test_known_audio_covers_all_four_vol_network_sports():
    # The Vol Network (confirmed via utsports.com) covers football, men's
    # and women's basketball, and baseball for Tennessee - each keyed to
    # that sport's OWN numeric id, not shared, since a school's id differs
    # per sport (see dynamic_teams.py). Tennessee happens to share "2633"
    # across football/men's/women's basketball but baseball is "199".
    assert ncaaf.known_audio("2633") is not None
    assert ncaamb.known_audio("2633") is not None
    assert ncaawb.known_audio("2633") is not None
    assert ncaabsb.known_audio("199") is not None


def test_known_audio_is_per_instance_not_shared_across_sports():
    # A school's numeric ESPN id differs per sport, so an NcaaLeague built
    # with no known_audio must never see another instance's table -
    # regression against a shared mutable default. Also confirms baseball's
    # id ("199") for Tennessee isn't accidentally present under men's
    # basketball, which uses "2633" for the same school.
    other = NcaaLeague("basketball", "mens-college-basketball")
    assert other.known_audio("2633") is None
    assert ncaamb.known_audio("199") is None
