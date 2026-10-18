# Telegram AI Bot

A macOS desktop app that embeds Telegram Web and answers the open chat automatically with Google Gemini. Replies are based on the full chat history plus a local knowledge base you manage in the app. The UI is in Persian (right-to-left).

## Features

- Telegram Web embedded on the right; the control panel is on the left.
- Reads earlier messages in the chat when started, then answers new incoming messages. Several quick messages get one combined reply.
- Knowledge base (prices, opening hours, address, …) stored in SQLite. Enabled items are used from the next reply on.
- Gemini with automatic fallback to other models; current date/time (Gregorian and Jalali) passed to the model.
- Activity feed that shows messages as chat bubbles, and errors with a plain-language fix (e.g. region block → use a VPN/proxy).
- Settings: API key with a connection test, proxy (for Telegram and Gemini), bot persona, models.

## Development

Requires Python 3.11+ and `make`. Run `make` to list all targets.

```bash
make install     # create .venv and install the app with dev tools
make run         # run the app from source
make check       # lint + unit tests (run before committing)
make test-gui    # Qt WebEngine integration tests (needs a display)
make build       # checks, then dist/TelegramAIBot.app and .dmg
make logs        # last lines of the app log
make clean       # remove build output and caches (distclean also removes .venv)
```

Without make: `pip install -e ".[dev]"`, then `python -m telegram_ai_bot`, `pytest`, `ruff check src tests`, `./scripts/build_macos.sh`.

The `.app` is ad-hoc signed (Apple Silicon). On another Mac, open it with right-click → Open, or run `xattr -cr /Applications/TelegramAIBot.app`.

## Releases

Releases are built and published by GitHub Actions:

```bash
make release VERSION=1.2.0
```

This runs the checks, bumps `__version__` in `src/telegram_ai_bot/__init__.py` (the single version source), commits, tags `v1.2.0` and pushes. The tag starts the **Release** workflow, which builds the app on an Apple Silicon macOS runner and publishes a GitHub Release with `TelegramAIBot-1.2.0-macos-arm64.dmg` and notes generated from the commits. The workflow refuses tags that don't match `__version__`.

The **CI** workflow runs lint and tests on every push to `master` and on every pull request. The Release workflow can also be started manually from the Actions tab; a manual run only uploads the DMG as a build artifact and publishes no release.

## Data

All user data lives in `~/Library/Application Support/TelegramAIBot/` (override with `TELEGRAM_AI_BOT_DATA_DIR`):

| Path | Contents |
|---|---|
| `knowledge.db` | knowledge base and settings (including the API key in plain text) |
| `webview_profile/` | Telegram Web session |
| `logs/app.log` | rotating application log |

## Project layout

```
src/telegram_ai_bot/
  config.py            constants (timings, Gemini defaults)
  paths.py             resource and user-data locations
  logging_setup.py
  core/                domain models, Jalali calendar, default prompt
  storage/             SQLite database with migrations; knowledge and settings repositories
  ai/                  Gemini REST client, typed errors, reply agent (prompt building, model fallback)
  telegram/            page scripts, TelegramPage interface + Qt WebEngine adapter, bot controller, events
  ui/                  theme, widgets, views, dialogs, main window; strings.py holds all Persian text
  resources/           bundled font (Vazirmatn, OFL) and icon
tests/                 unit tests; the bot runs against an in-memory fake Telegram page
packaging/             PyInstaller launcher and app icon
scripts/build_macos.sh
Makefile               development and release tasks
.github/workflows/     CI (lint + tests) and tag-triggered macOS release
```

### Design notes

- **The bot is decoupled from the browser.** `BotController` talks to a `TelegramPage` protocol (`read_state`, `scroll_history`, `send_message`). The app uses `WebEngineTelegramPage`; tests use a fake page.
- **Events, not text.** The controller emits `BotEvent`s. `ui/strings.describe_event` turns them into Persian text, so no Persian appears outside the UI layer.
- **Settings and knowledge are read again for every reply**, so changes apply without restarting.
- **If Telegram changes its markup**, only the selectors at the top of `telegram/scripts.py` should need updating. The GUI tests check the scripts against a copy of the expected markup.
- **Shutdown order matters.** The browser profile is owned by the application and deleted after the window. Deleting it first can corrupt the Telegram session.
