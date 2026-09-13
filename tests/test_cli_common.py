import argparse

import pytest

from sports_near_me.cli_common import (
    DEFAULT_CONFIG_CONTENTS, DEFAULTS, _create_default_config_file,
    add_shared_flags, configure_logging, load_config_file, resolve_settings,
)


def _parse(argv):
    parser = argparse.ArgumentParser()
    add_shared_flags(parser)
    return parser.parse_args(argv)


def test_no_config_at_default_path_creates_one_with_a_starter_follow_list(tmp_path, monkeypatch):
    # This is the first-run experience: nothing at the default path yet.
    # resolve_settings() should create a real, usable config there and
    # use it immediately - not leave this run with an empty follow list
    # that only gets fixed on the *next* run.
    default_path = tmp_path / "missing.yaml"
    monkeypatch.setattr("sports_near_me.cli_common.DEFAULT_CONFIG_PATH", default_path)

    settings = resolve_settings(_parse([]))

    assert default_path.exists()
    assert settings["_config_created"] is True
    assert settings["_config_path"] == str(default_path)
    assert settings["week"] is None
    assert settings["log_level"] == "INFO"
    # The requested starter list, exactly - each sport keyed correctly.
    follow = settings["_follow"]
    assert follow["nfl"]["teams"] == ["Bears"]
    assert follow["mlb"]["teams"] == ["Cubs"]
    assert follow["nhl"]["teams"] == ["Blackhawks"]
    assert follow["ncaamb"]["teams"] == ["Tennessee", "Wisconsin"]
    assert follow["ncaawb"]["teams"] == ["Tennessee", "Wisconsin"]
    assert follow["ncaavbw"]["teams"] == ["Tennessee", "Wisconsin"]


def test_default_config_is_only_created_once(tmp_path, monkeypatch):
    # A second run against the same (now-existing) default path must load
    # it normally, not recreate it or report _config_created again -
    # otherwise the "we created a file for you" notice would repeat forever.
    default_path = tmp_path / "missing.yaml"
    monkeypatch.setattr("sports_near_me.cli_common.DEFAULT_CONFIG_PATH", default_path)

    first = resolve_settings(_parse([]))
    assert first["_config_created"] is True
    created_at = default_path.read_text()

    second = resolve_settings(_parse([]))
    assert second["_config_created"] is False
    assert second["_config_path"] == str(default_path)
    assert default_path.read_text() == created_at  # untouched, not rewritten


def test_create_default_config_file_writes_valid_parseable_yaml(tmp_path):
    path = tmp_path / "new_config.yaml"
    assert _create_default_config_file(path) is True
    assert path.exists()
    # Must actually parse as YAML, not just be the right literal string -
    # this is what a real run would load.
    loaded = load_config_file(path)
    assert loaded["follow"]["nfl"]["teams"] == ["Bears"]
    assert path.read_text() == DEFAULT_CONFIG_CONTENTS


def test_create_default_config_file_failure_is_non_fatal(tmp_path):
    # An unwritable location (parent directory doesn't exist) shouldn't
    # crash the whole run - resolve_settings() falls back to an empty
    # follow list instead, same as if no file existed at all.
    unwritable = tmp_path / "no" / "such" / "dir" / "config.yaml"
    assert _create_default_config_file(unwritable) is False


def test_explicit_config_still_created_when_missing_would_not_apply(tmp_path, monkeypatch):
    # Auto-creation is ONLY for the default path - an explicitly-passed
    # --config that doesn't exist is still a real error, not something to
    # silently paper over with a generated file. (Regression guard: this
    # already worked before auto-creation existed - see
    # test_missing_explicit_config_raises below - but worth reasserting
    # here since both branches live in the same if/elif chain.)
    monkeypatch.setattr("sports_near_me.cli_common.DEFAULT_CONFIG_PATH", tmp_path / "unrelated.yaml")
    missing = tmp_path / "nope.yaml"
    with pytest.raises(FileNotFoundError):
        resolve_settings(_parse(["--config", str(missing)]))
    assert not missing.exists()


def test_config_file_supplies_shared_defaults_and_follow_list(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(
        "tz: America/Chicago\n"
        "log_level: DEBUG\n"
        "follow:\n"
        "  nfl:\n"
        "    teams: [Bears]\n"
        "  ncaaf:\n"
        "    conferences: [SEC, Big Ten]\n"
    )
    settings = resolve_settings(_parse(["--config", str(config)]))
    assert settings["tz"] == "America/Chicago"
    assert settings["log_level"] == "DEBUG"
    assert settings["_follow"]["nfl"]["teams"] == ["Bears"]
    assert settings["_follow"]["ncaaf"]["conferences"] == ["SEC", "Big Ten"]
    assert settings["_config_path"] == str(config)


def test_cli_flag_overrides_config_file(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("tz: America/Chicago\n")
    settings = resolve_settings(_parse(["--config", str(config), "--tz", "America/New_York"]))
    assert settings["tz"] == "America/New_York"


def test_provenance_tracks_default_config_and_cli_sources(tmp_path):
    # This is what --explain reads (see cli.py's _print_explain()) - a
    # per-setting record of whether the final value came from the CLI, the
    # config file, or was never set at all.
    config = tmp_path / "config.yaml"
    config.write_text("tz: America/Chicago\nlog_level: DEBUG\n")
    settings = resolve_settings(_parse(["--config", str(config), "--tz", "America/New_York"]))
    provenance = settings["_provenance"]
    assert provenance["tz"] == "cli"  # CLI --tz beat the config's tz
    assert provenance["log_level"] == "config"  # untouched by any CLI flag
    assert provenance["week"] == "default"  # never set anywhere
    assert provenance["range"] == "default"
    assert provenance["log_dir"] == "default"


def test_provenance_notes_verbose_and_silent_shortcuts_specifically():
    assert resolve_settings(_parse(["--verbose"]))["_provenance"]["log_level"] == "cli (--verbose)"
    assert resolve_settings(_parse(["--silent"]))["_provenance"]["log_level"] == "cli (--silent)"


def test_missing_explicit_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        resolve_settings(_parse(["--config", str(tmp_path / "nope.yaml")]))


def test_verbose_shortcut_sets_debug():
    assert resolve_settings(_parse(["--verbose"]))["log_level"] == "DEBUG"


def test_silent_shortcut_sets_error():
    assert resolve_settings(_parse(["--silent"]))["log_level"] == "ERROR"


def test_verbose_and_log_level_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        _parse(["--verbose", "--log-level", "DEBUG"])


def test_configure_logging_writes_file(tmp_path):
    settings = dict(DEFAULTS)
    settings["log_dir"] = str(tmp_path)
    logger = configure_logging(settings)
    logger.info("test message")
    for handler in logger.handlers:
        handler.flush()
    log_files = list(tmp_path.glob("sports_near_me_*.log"))
    assert len(log_files) == 1
    assert "test message" in log_files[0].read_text()
