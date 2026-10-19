# Share

Small static files and collectible cards, hosted by GitHub Pages.

Live collection: https://pkronstrom.github.io/share/

## Quick CLI

Requires Python 3, Git, an authenticated `gh` CLI, and push access to this repository. Run from this checkout, or symlink `quick-share` into your PATH.

```sh
./quick-share publish /path/to/card.html --name foxyasset --preview /path/to/preview.png
./quick-share list
./quick-share publish /path/to/updated.html --name foxyasset --replace
./quick-share unshare foxyasset
```

Publishing commits and pushes the selected file, then waits up to four minutes for the matching Pages build. HTML appears at `/cards/NAME/`; other files retain their filename. `--preview` adds social link metadata and a preview image. The self-contained HTML still carries its original asset bundle.

Use `--dry-run` to inspect an action without changing anything. `--no-push` commits locally only. Repeating the same publication is a no-op; replacing different content requires `--replace`. The CLI refuses to start with a dirty working tree and never stages unrelated files. If a push fails, retrying the same command pushes the existing local commit.

Shares are public and persist until removed. Unsharing removes the live page after a Pages deployment; it does not erase Git history, caches, forks or downloaded copies. There is no automatic expiry. Only publish files you intend to make public. Asset-specific reuse terms remain in each card; this repository grants no blanket license to its contents.

Tests: `python3 tests/test_cli.py`.
