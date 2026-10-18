"""Main window: Telegram Web on the right, the control panel on the left."""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter, QWidget

from telegram_ai_bot import config, paths
from telegram_ai_bot.ai.agent import ReplyAgent
from telegram_ai_bot.storage.knowledge import KnowledgeRepository
from telegram_ai_bot.storage.settings import SettingsRepository
from telegram_ai_bot.telegram.bot import BotController
from telegram_ai_bot.telegram.events import BotEvent, EventType
from telegram_ai_bot.telegram.page import WebEngineTelegramPage
from telegram_ai_bot.ui import strings
from telegram_ai_bot.ui.settings_dialog import SettingsDialog
from telegram_ai_bot.ui.side_panel import SidePanel


def create_telegram_view(parent: QWidget) -> QWebEngineView:
    # Persistent profile so the Telegram login survives restarts. Its parent is the application
    # (not the window) so it outlives the page; deleting it first can corrupt the stored session.
    profile = QWebEngineProfile("telegram", QApplication.instance())
    profile.setPersistentStoragePath(str(paths.browser_profile_dir()))
    profile.setCachePath(str(paths.browser_profile_dir() / "cache"))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
    profile.setHttpUserAgent(config.USER_AGENT)

    view = QWebEngineView(parent)
    view.setPage(QWebEnginePage(profile, view))
    view.setLayoutDirection(Qt.LeftToRight)
    view.load(QUrl(config.TELEGRAM_URL))
    return view


class MainWindow(QMainWindow):
    def __init__(self, settings_repo: SettingsRepository, knowledge_repo: KnowledgeRepository):
        super().__init__()
        self._settings_repo = settings_repo
        self.setWindowTitle(strings.APP_TITLE)
        self.setWindowIcon(QIcon(str(paths.RESOURCES_DIR / "icon.png")))
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)

        self.view = create_telegram_view(self)
        # Settings and knowledge are re-read for every reply so edits apply immediately.
        self.bot = BotController(
            WebEngineTelegramPage(self.view.page()),
            responder_factory=lambda: ReplyAgent(settings_repo.load(), knowledge_repo.enabled()),
            parent=self,
        )
        self.panel = SidePanel(self.bot, knowledge_repo)
        self.panel.setMinimumWidth(400)
        self.panel.setMaximumWidth(560)
        self.panel.settings_requested.connect(self._open_settings)
        self.panel.reload_requested.connect(self.view.reload)
        self.view.loadFinished.connect(self._on_page_loaded)

        # In a right-to-left layout the first widget is placed on the right.
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(self.view)
        splitter.addWidget(self.panel)
        splitter.setSizes([1000, 440])
        splitter.setStretchFactor(0, 1)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        self.setCentralWidget(splitter)

    def _open_settings(self) -> None:
        SettingsDialog(self._settings_repo, self).exec()

    def _on_page_loaded(self, ok: bool) -> None:
        if not ok:
            self.panel.activity.add_event(BotEvent(EventType.PAGE_LOAD_FAILED))
            self.panel.show_activity()

    def closeEvent(self, event) -> None:
        self.bot.shutdown()
        super().closeEvent(event)
