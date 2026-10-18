"""Filesystem locations for bundled resources and per-user data."""

import os
import sys
from pathlib import Path

APP_ID = "TelegramAIBot"
DATA_DIR_ENV = "TELEGRAM_AI_BOT_DATA_DIR"

PACKAGE_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = PACKAGE_DIR / "resources"


def data_dir() -> Path:
    """Directory for the database, browser profile and logs.

    Lives outside the app bundle so updates never wipe user data.
    Can be overridden with TELEGRAM_AI_BOT_DATA_DIR (used by tests).
    """
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        path = Path(override)
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / APP_ID
    elif sys.platform == "win32":
        path = Path(os.environ.get("APPDATA", Path.home())) / APP_ID
    else:
        path = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return data_dir() / "knowledge.db"


def browser_profile_dir() -> Path:
    return data_dir() / "webview_profile"


def log_dir() -> Path:
    path = data_dir() / "logs"
    path.mkdir(exist_ok=True)
    return path
