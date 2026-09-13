# Man pages

Real troff man pages, for viewing in a terminal. If you're reading docs in
PyCharm (or anywhere else that doesn't render troff), use the Markdown
versions in the parent [`docs/`](../) directory instead — same content,
kept in sync by hand:

| Man page | Markdown equivalent |
|---|---|
| `sports-game.1` | [`../CLI.md`](../CLI.md) |
| `sports_near_me.yaml.5` | [`../CONFIG.md`](../CONFIG.md) |
| `sports-game-launchers.7` | [`../LAUNCHERS.md`](../LAUNCHERS.md) |

## Viewing these locally

Without installing them anywhere:

```bash
mandoc -T ascii docs/man/sports-game.1 | less
```

(or `groff -man -Tutf8` if you have groff instead of `mandoc`/`man-db`).

To install them so plain `man sports-game` works, copy them onto your
`MANPATH` following your OS's convention — e.g. on most Linux/macOS setups:

```bash
sudo cp docs/man/sports-game.1 /usr/local/share/man/man1/
sudo cp docs/man/sports_near_me.yaml.5 /usr/local/share/man/man5/
sudo cp docs/man/sports-game-launchers.7 /usr/local/share/man/man7/
sudo mandb 2>/dev/null || sudo makewhatis 2>/dev/null  # refresh the index, name varies by OS
```
