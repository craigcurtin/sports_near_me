import pytest

from sports_near_me import cli
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
    with pytest.raises(ValueError, match=r"ESPN's NFL data doesn't have a team called"):
        _resolve_explicit_teams(nfl, "bears,not-a-real-team")


def test_resolve_explicit_teams_raises_on_ambiguous_name():
    with pytest.raises(ValueError, match="matches more than one team"):
        _resolve_explicit_teams(nfl, "bears,new york")


def test_explain_never_fetches_a_schedule(tmp_path, monkeypatch, capsys):
    # The entire point of --explain is that it's safe/instant to run - no
    # network call, no dependence on ESPN being up. fetch_schedule raising
    # if called at all is the strongest way to prove that.
    def _boom(*a, **kw):
        raise AssertionError("--explain must never call fetch_schedule")
    monkeypatch.setattr(cli, "fetch_schedule", _boom)

    config = tmp_path / "config.yaml"
    config.write_text("follow:\n  nfl:\n    teams: [Bears]\n")
    assert cli.run(["--explain", "--config", str(config), "--silent"]) == 0
    assert "Fetched" not in capsys.readouterr().out


def test_explain_no_sport_lists_every_sport_in_the_config_follow_list(tmp_path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text(
        "follow:\n"
        "  nfl:\n    teams: [Bears]\n"
        "  mlb:\n    teams: [Cubs, Brewers]\n"
        "  ncaaf:\n    teams: [Tennessee]\n    conferences: [SEC, Big Ten]\n"
    )
    assert cli.run(["--explain", "--config", str(config), "--silent"]) == 0
    out = capsys.readouterr().out
    assert "nfl: teams: Bears" in out
    assert "mlb: teams: Cubs, Brewers" in out
    assert "ncaaf: teams: Tennessee" in out
    assert "ncaaf: conferences: SEC, Big Ten" in out
    assert "source: config (follow.nfl.teams)" in out
    assert "source: config (follow.ncaaf.conferences)" in out


def test_explain_explicit_cli_team_overrides_config_source(tmp_path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text("follow:\n  mlb:\n    teams: [Cubs]\n")
    assert cli.run(["mlb", "cubs", "brewers", "--explain",
                     "--config", str(config), "--silent"]) == 0
    out = capsys.readouterr().out
    assert "mlb: cubs, brewers" in out
    assert "source: cli (explicit team argument" in out
    assert "follow.mlb.teams" not in out  # config's list is fully bypassed, not just supplemented


def test_explain_notes_unconfigured_sport_would_fail(tmp_path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text("follow:\n  mlb:\n    teams: [Cubs]\n")
    assert cli.run(["nhl", "--explain", "--config", str(config), "--silent"]) == 0
    out = capsys.readouterr().out
    assert "nhl: (nothing configured)" in out
    assert "would fail" in out


def test_explain_reports_provenance_for_a_cli_overridden_setting(tmp_path, capsys):
    config = tmp_path / "config.yaml"
    config.write_text("tz: America/Chicago\nfollow:\n  nfl:\n    teams: [Bears]\n")
    assert cli.run(["--explain", "--config", str(config), "--tz", "America/New_York"]) == 0
    out = capsys.readouterr().out
    assert "America/New_York" in out
    # The line naming the tz setting should attribute it to the CLI, not the config.
    tz_line = next(line for line in out.splitlines() if line.startswith("tz "))
    assert "cli" in tz_line
    assert "config" not in tz_line
