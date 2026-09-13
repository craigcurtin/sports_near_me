import argparse

import pytest

from sports_near_me.cli_common import DEFAULTS, add_shared_flags, configure_logging, resolve_settings


def _parse(argv):
    parser = argparse.ArgumentParser()
    add_shared_flags(parser)
    return parser.parse_args(argv)


def test_defaults_with_no_config(tmp_path, monkeypatch):
    monkeypatch.setattr("sports_near_me.cli_common.DEFAULT_CONFIG_PATH", tmp_path / "missing.yaml")
    settings = resolve_settings(_parse([]))
    assert settings["week"] is None
    assert settings["log_level"] == "INFO"
    assert settings["_config_path"] is None
    assert settings["_follow"] == {}


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
