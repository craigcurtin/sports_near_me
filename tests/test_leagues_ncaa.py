from unittest.mock import patch

import pytest

from sports_near_me.leagues import LEAGUES, ncaabsb, ncaaf, ncaamb, ncaamh, ncaamsoc, ncaavbm, ncaavbw, ncaawb, ncaawsoc
from sports_near_me.leagues._ncaa import NcaaLeague
from sports_near_me.resolve import Team


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
    other = NcaaLeague("basketball", "mens-college-basketball", "NCAA men's basketball")
    assert other.known_audio("2633") is None
    assert ncaamb.known_audio("199") is None


def test_known_audio_covers_wisconsin_badger_radio_network_sports():
    # Confirmed via research: Matt Lepay calls football + men's basketball,
    # Jon Arias calls women's basketball + volleyball, Brian Posick calls
    # men's hockey - all the same "Wisconsin Badgers Sports Network," which
    # is why the station name/URL repeats across these entries rather than
    # needing separate verification per sport.
    for league in (ncaaf, ncaamb, ncaawb, ncaamh, ncaavbw):
        station, url = league.known_audio("275")
        assert "Wisconsin" in station
        assert url.startswith("https://")


def test_resolve_team_not_found_names_this_specific_ncaa_sport():
    # Regression for a real-world case: Tennessee has no NCAA men's hockey
    # team (confirmed absent from ESPN's own 116-team list), so the error
    # should say exactly that - not a generic "not recognized" that reads
    # like a typo when the real issue is the team genuinely doesn't play
    # this sport with this data provider.
    fake_teams = [Team(id="275", display_name="Wisconsin Badgers", search_keys=("wisconsin", "badgers"))]
    with patch("sports_near_me.leagues._ncaa.fetch_all_teams", return_value=fake_teams):
        with pytest.raises(ValueError,
                            match=r"ESPN's NCAA men's hockey data doesn't have a team called 'Tennessee'"):
            ncaamh.resolve_team("Tennessee")


def test_known_audio_wisconsin_has_no_mens_volleyball_entry():
    # Deliberate absence, not an oversight: Wisconsin doesn't field a
    # men's volleyball program at all (confirmed absent from ESPN's own
    # mens-college-volleyball team list) - the Badgers are a women's
    # volleyball power, not a men's program, so there's nothing true to
    # verify and add here.
    assert ncaavbm.known_audio("275") is None


def test_soccer_leagues_registered_with_espns_actual_slugs():
    # Soccer is the one NCAA sport whose ESPN league slug doesn't follow
    # the "{gender}-college-{sport}" pattern every other sport here uses -
    # verified live (see leagues/__init__.py) against
    # apis/site/v2/sports/soccer/usa.ncaa.{w,m}.1/teams, which returned
    # real team lists (417 women's, 270 men's).
    assert ncaawsoc.SPORT == "soccer" and ncaawsoc.LEAGUE == "usa.ncaa.w.1"
    assert ncaamsoc.SPORT == "soccer" and ncaamsoc.LEAGUE == "usa.ncaa.m.1"
    assert LEAGUES["ncaawsoc"] is ncaawsoc
    assert LEAGUES["ncaamsoc"] is ncaamsoc


def test_soccer_resolve_not_found_names_the_right_sport():
    fake_teams = [Team(id="1", display_name="East Tennessee State", search_keys=("etsu", "east tennessee state"))]
    with patch("sports_near_me.leagues._ncaa.fetch_all_teams", return_value=fake_teams):
        with pytest.raises(ValueError,
                            match=r"ESPN's NCAA men's soccer data doesn't have a team called 'Wisconsin'"):
            ncaamsoc.resolve_team("Wisconsin")
