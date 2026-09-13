"""
Shared CLI plumbing: YAML config loading/merging and logging setup, split
out from cli.py so "how do defaults get resolved" and "how does logging get
configured" aren't tangled up with the report itself.

The config file's 'follow:' section is the interesting part: per sport, a
list of specific teams and/or whole conferences (e.g. follow.ncaaf.teams:
[Notre Dame], follow.ncaaf.conferences: [SEC, Big Ten]). Nothing here
resolves those names to ids - that happens fresh in cli.py/leagues each
run (see conferences.py's and dynamic_teams.py's docstrings for why: an id
is never persisted anywhere, so there's nothing to go stale).
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DEFAULT_CONFIG_PATH = Path.home() / ".sports_near_me.yaml"
LOG_LEVEL_CHOICES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Every flag defaults to None (not this dict's value) on the argparse side -
# that's what lets resolve_settings() tell "user didn't pass this" apart
# from "user explicitly chose the default."
DEFAULTS = {
    "week": None,
    "range": None,
    "tz": None,
    "log_dir": None,
    "log_level": "INFO",
}

logger = logging.getLogger("sports_near_me")


def _parse_day_range(value: str) -> int:
    """Accepts '7d', '7', 'D7' etc. - just a count of days with an
    optional 'd' suffix, not a full duration-string parser. Rejects
    anything under 1 day; there's no such thing as a zero-day window."""
    text = value.strip().lower().removesuffix("d")
    try:
        days = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid --range {value!r} - expected a number of days, e.g. '1d' or '7d'")
    if days < 1:
        raise argparse.ArgumentTypeError(f"--range must be at least 1 day, got {value!r}")
    return days


def add_shared_flags(parser: argparse.ArgumentParser) -> None:
    """Flags every invocation shares, whether or not a sport subcommand is
    given - attached to both the top-level parser (for the no-subcommand
    "everything I follow" mode) and every per-sport subparser."""
    parser.add_argument("--config", default=None,
                         help=f"Path to a YAML config file. Default: {DEFAULT_CONFIG_PATH} if it exists.")
    # Mutually exclusive: each is a different way of picking WHICH game(s)
    # to show, so combining them is ambiguous about intent - same
    # reasoning as the log-level group below. Default (none given): just
    # the single next upcoming game.
    which_game = parser.add_mutually_exclusive_group()
    which_game.add_argument("--week", type=int, default=None,
                             help="Show a specific numbered week's game instead of the next "
                                  "upcoming one (football only - other sports ignore this).")
    which_game.add_argument("--range", type=_parse_day_range, default=None, metavar="Nd",
                             help="Show every game in a rolling window starting today, e.g. "
                                  "'1d' (today only, including games already finished earlier "
                                  "today) or '7d' (this week). By calendar date in the display "
                                  "timezone (see --tz). Can be more than one game for sports "
                                  "that play daily, e.g. MLB.")
    parser.add_argument("--tz", default=None,
                         help="IANA timezone for kickoff time (e.g. 'America/New_York'). "
                              "Default: this machine's local timezone - the zone actually used "
                              "is always shown (e.g. 'EDT'), so set this explicitly if you want "
                              "a specific zone regardless of what machine runs the command.")
    parser.add_argument("--log-dir", default=None,
                         help="Directory to write a timestamped diagnostic log file to. "
                              "Default: none (stderr only).")
    # Mutually exclusive, same reasoning as PortfolioLens's cli_common.py:
    # combining any two of these is ambiguous about intent, so argparse
    # rejects it rather than silently picking one. None of these touch the
    # report itself (always printed to stdout) - only diagnostic verbosity.
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("--log-level", choices=LOG_LEVEL_CHOICES, default=None,
                            help="Minimum severity to emit to stderr/log file (default: INFO).")
    verbosity.add_argument("--verbose", "-v", action="store_true", default=False,
                            help="Shortcut for --log-level DEBUG.")
    verbosity.add_argument("--silent", "-s", action="store_true", default=False,
                            help="Shortcut for --log-level ERROR - only the report and real errors print.")


def load_config_file(path: Path) -> dict:
    if yaml is None:
        raise ImportError("pyyaml is not installed. Run: pip install pyyaml")
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def resolve_settings(args: argparse.Namespace) -> dict:
    """Merges DEFAULTS <- config file (if one exists) <- CLI flags (CLI
    always wins). An explicitly-passed --config that doesn't exist is an
    error worth surfacing; the default path silently existing-or-not is
    fine, since most people won't have created it yet."""
    settings = dict(DEFAULTS)

    config_arg = getattr(args, "config", None)
    config_path = Path(config_arg).expanduser() if config_arg else DEFAULT_CONFIG_PATH
    config = {}
    if config_path.exists():
        config = load_config_file(config_path)
        settings["_config_path"] = str(config_path)
    elif config_arg:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    else:
        settings["_config_path"] = None

    for key in ("tz", "log_level", "log_dir"):
        if key in config:
            settings[key] = config[key]

    settings["_follow"] = config.get("follow", {})

    for key in DEFAULTS:
        cli_value = getattr(args, key, None)
        if cli_value is not None:
            settings[key] = cli_value

    if getattr(args, "verbose", False):
        settings["log_level"] = "DEBUG"
    elif getattr(args, "silent", False):
        settings["log_level"] = "ERROR"

    return settings


def configure_logging(settings: dict) -> logging.Logger:
    """Diagnostics (config resolved, team matched, schedule fetched,
    unhandled errors) go to stderr and, if log_dir is set, to a timestamped
    file too - kept separate from stdout, which is always exactly the game
    report and nothing else."""
    level = getattr(logging, settings["log_level"].upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")

    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    if settings.get("log_dir"):
        log_dir = Path(settings["log_dir"]).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(log_dir / f"sports_near_me_{timestamp}.log")
        file_handler.setLevel(logging.DEBUG)  # file always keeps full detail regardless of console level
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
