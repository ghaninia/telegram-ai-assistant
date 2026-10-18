"""Access to the Telegram Web page. The bot depends on the TelegramPage protocol, not on Qt WebEngine."""

from collections.abc import Callable
from typing import Protocol

from PySide6.QtWebEngineCore import QWebEnginePage

from telegram_ai_bot.core.models import ChatState
from telegram_ai_bot.telegram import scripts

StateCallback = Callable[[ChatState], None]


class TelegramPage(Protocol):
    def read_state(self, callback: StateCallback) -> None: ...

    def scroll_history(self, to_top: bool) -> None: ...

    def send_message(self, text: str) -> None: ...


class WebEngineTelegramPage:
    """TelegramPage backed by a QWebEnginePage showing web.telegram.org."""

    def __init__(self, page: QWebEnginePage):
        self._page = page

    def _run(self, script: str, callback: Callable[[object], None] | None = None) -> None:
        self._page.runJavaScript(script, 0, callback or (lambda _: None))

    def read_state(self, callback: StateCallback) -> None:
        self._run(scripts.STATE_SCRIPT, lambda raw: callback(ChatState.from_json(raw)))

    def scroll_history(self, to_top: bool) -> None:
        self._run(scripts.scroll_script(to_top))

    def send_message(self, text: str) -> None:
        self._run(scripts.send_script(text))
