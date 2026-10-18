"""Application entry point and composition root."""

import logging
import os
import sys

import shiboken6
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from telegram_ai_bot import __version__, paths
from telegram_ai_bot.logging_setup import configure_logging
from telegram_ai_bot.storage.database import Database
from telegram_ai_bot.storage.knowledge import KnowledgeRepository
from telegram_ai_bot.storage.settings import SettingsRepository
from telegram_ai_bot.ui import strings
from telegram_ai_bot.ui.main_window import MainWindow
from telegram_ai_bot.ui.theme import apply_theme

log = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    log.info("starting v%s, data dir %s", __version__, paths.data_dir())

    db = Database(paths.database_path())
    settings_repo = SettingsRepository(db)
    knowledge_repo = KnowledgeRepository(db)

    # Chromium reads its proxy from flags, which must be set before QApplication exists.
    proxy = settings_repo.load().proxy
    if proxy:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"--proxy-server={proxy}"

    app = QApplication(sys.argv)
    app.setApplicationName(strings.APP_TITLE)
    app.setLayoutDirection(Qt.RightToLeft)
    apply_theme(app)

    window = MainWindow(settings_repo, knowledge_repo)
    window.show()
    exit_code = app.exec()
    # Delete the window (and its web page) before the browser profile owned by the app.
    shiboken6.delete(window)
    sys.exit(exit_code)
