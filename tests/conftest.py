import gc
import os
import time

import pytest

# Widget tests run headless unless GUI tests (which need a real display) are requested.
if not os.environ.get("RUN_GUI_TESTS"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from telegram_ai_bot.core.models import ChatMessage, ChatState, Direction  # noqa: E402
from telegram_ai_bot.storage.database import Database  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Never touch the real user data directory."""
    monkeypatch.setenv("TELEGRAM_AI_BOT_DATA_DIR", str(tmp_path / "data"))


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app
    # Destroy leftover widgets while the application still exists.
    for widget in app.topLevelWidgets():
        widget.deleteLater()
    app.processEvents()
    gc.collect()


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "test.db")


def wait_until(predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError("condition not met in time")
        QApplication.processEvents()
        time.sleep(0.005)


def msg(mid: str, text: str, incoming: bool = True) -> ChatMessage:
    return ChatMessage(mid, Direction.INCOMING if incoming else Direction.OUTGOING, text)


class FakeTelegramPage:
    """In-memory TelegramPage. Callbacks are delivered asynchronously like the real page."""

    def __init__(self, messages=(), *, logged_in=True, chat_id="#@ali", title="Ali", older=()):
        self.logged_in = logged_in
        self.chat_id = chat_id
        self.title = title
        self.messages = list(messages)
        self.older = list(older)  # revealed by scrolling to the top
        self.sent: list[str] = []
        self.scrolls: list[bool] = []
        self._next_id = 1000

    def read_state(self, callback) -> None:
        state = ChatState(self.logged_in, self.chat_id, self.title, tuple(self.messages))
        QTimer.singleShot(0, lambda: callback(state))

    def scroll_history(self, to_top: bool) -> None:
        self.scrolls.append(to_top)
        if to_top and self.older:
            self.messages = self.older + self.messages
            self.older = []

    def send_message(self, text: str) -> None:
        self.sent.append(text)
        self.messages.append(msg(str(self._next_id), text, incoming=False))
        self._next_id += 1

    def receive(self, text: str) -> None:
        self.messages.append(msg(str(self._next_id), text))
        self._next_id += 1
