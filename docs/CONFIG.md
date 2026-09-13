# sports_near_me.yaml(5)

Config file for [`sports-game`](CLI.md), read on every invocation.

A YAML file of shared defaults and a per-sport **follow** list. Every key
is optional. A command-line flag always overrides the matching shared key;
the follow list is only consulted when no team is given on the command
line.

The file is looked up at `~/.sports_near_me.yaml` by default, or at the
path given with `sports-game`'s `--config` flag. Passing `--config` with a
path that doesn't exist is an error; the default path silently not
existing is not — most people won't have created it yet.

## Shared keys

| Key | Meaning |
|---|---|
| `tz` | IANA timezone string (e.g. `America/New_York`) used for every printed kickoff time. Overridden by `--tz`. Default: **UTC** - never guessed from the machine's own clock, since this file can be copied to a different machine/location. Set this to see local kickoff times. |
| `log_level` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Default: `INFO`. |
| `log_dir` | Directory to also write a timestamped diagnostic log file to. Default: none (stderr only). |

## The follow list

`follow` is a mapping from sport key (`nfl`, `mlb`, `nhl`, `ncaaf`,
`ncaamb`, `ncaawb`, `ncaabsb`, `ncaamh`, `ncaavbw`, `ncaavbm` — see
[CLI.md](CLI.md#sports)) to an object with either or both of:

- **`teams`** — a list of team names, in the same loose form `sports-game`
  accepts on the command line (nickname, city, full name, or abbreviation).
- **`conferences`** — a list of conference names (e.g. `SEC`, `Big Ten`,
  `ACC`). **NCAA sports only** — `nfl`, `mlb`, and `nhl` have no conference
  concept here, and any entry under their `conferences` key is skipped
  with a warning, not an error.

Following a conference follows every current member team's **entire**
schedule, including non-conference and cross-conference games — not just
games against other conference members. Membership is looked up fresh
each run (see [Nothing here is a cached id](#nothing-here-is-a-cached-id)),
so realignment is reflected automatically.

A team reachable both directly (under `teams`) and via a followed
conference is only shown once.

## Example

```yaml
tz: America/New_York
log_level: INFO
# log_dir: ~/.sports_near_me/logs

follow:
  nfl:
    teams: [Bears]
  mlb:
    teams: [Cubs]
  nhl:
    teams: [Blackhawks]
  ncaaf:
    teams: [Notre Dame]          # independent - not in any conference
    conferences: [SEC, Big Ten]
  ncaamb:
    conferences: [ACC]            # every ACC team - Duke, UNC, Louisville...
  ncaawb:
    teams: [Duke]
```

## Nothing here is a cached id

Nothing under `follow` is, or ever becomes, a stored id. Every team and
conference name here is re-resolved against ESPN's live data on each run
of `sports-game` — this file only ever holds what a person typed. See
[EXTENDING.md](EXTENDING.md#why-nothing-is-ever-cached-as-an-id) for why
that matters.

## See also

[CLI.md](CLI.md) · [LAUNCHERS.md](LAUNCHERS.md) · [EXTENDING.md](EXTENDING.md)
