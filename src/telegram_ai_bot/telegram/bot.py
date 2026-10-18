"""Bot controller: watches the open Telegram chat and answers new incoming messages."""

import logging
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Protocol

from PySide6.QtCore import QObject, QTimer, Signal

from telegram_ai_bot import config
from telegram_ai_bot.ai.errors import AIError, AIErrorKind
from telegram_ai_bot.core.models import ChatMessage, ChatState
from telegram_ai_bot.telegram.events import BotEvent, BotStatus, EventType
from telegram_ai_bot.telegram.page import TelegramPage

log = logging.getLogger(__name__)


class Responder(Protocol):
    def reply(self, messages: Sequence[ChatMessage]) -> str | None: ...


@dataclass(frozen=True, slots=True)
class BotTiming:
    poll_ms: int = config.POLL_INTERVAL_MS
    debounce_ms: int = config.DEBOUNCE_MS
    history_scrolls: int = config.HISTORY_SCROLLS
    scroll_wait_ms: int = config.HISTORY_SCROLL_WAIT_MS
    settle_ms: int = 800


class BotController(QObject):
    event = Signal(object)  # BotEvent
    status_changed = Signal(object)  # BotStatus
    chat_changed = Signal(str)  # title of the chat being answered
    replied = Signal()
    _reply_ready = Signal(object)  # str | None | Exception, delivered on the GUI thread

    def __init__(self, page: TelegramPage, responder_factory: Callable[[], Responder],
                 timing: BotTiming | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self._page = page
        self._responder_factory = responder_factory
        self._timing = timing = timing or BotTiming()
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ai")

        self.running = False
        self.status = BotStatus.OFF
        self._busy = False  # loading history or waiting for the model
        self._chat_id = ""
        self._seen: set[str] = set()
        self._warned_chat_switch = False
        self._last_error = ""

        self._poll_timer = QTimer(self, interval=timing.poll_ms)
        self._poll_timer.timeout.connect(self._poll)
        self._debounce = QTimer(self, singleShot=True, interval=timing.debounce_ms)
        self._debounce.timeout.connect(self._respond)
        self._reply_ready.connect(self._on_reply_ready)

    # ----- public API -----

    def start(self, reply_to_pending: bool) -> None:
        def on_state(state: ChatState) -> None:
            if not state.logged_in:
                self._emit(EventType.NOT_LOGGED_IN)
                return
            if not state.has_open_chat:
                self._emit(EventType.NO_CHAT_OPEN)
                return
            log.info("starting on chat %r", state.title)
            self.running = True
            self._busy = True
            self._chat_id = state.chat_id
            self._warned_chat_switch = False
            self._last_error = ""
            self.chat_changed.emit(state.title)
            self._set_status(BotStatus.LOADING)
            self._emit(EventType.STARTED, text=state.title)
            self._load_history(self._timing.history_scrolls, -1, lambda: self._finish_start(reply_to_pending))

        self._page.read_state(on_state)

    def stop(self) -> None:
        if not self.running:
            return
        log.info("stopped")
        self.running = False
        self._busy = False
        self._poll_timer.stop()
        self._debounce.stop()
        self._set_status(BotStatus.OFF)
        self._emit(EventType.STOPPED)

    def reply_now(self) -> None:
        """Answer the open chat once, right now, even when the bot is stopped."""
        if self._busy:
            self._emit(EventType.BUSY)
            return

        def on_state(state: ChatState) -> None:
            if not state.has_open_chat:
                self._emit(EventType.NO_CHAT_OPEN)
                return
            if not self.running:
                self.chat_changed.emit(state.title)
            self._respond(force=True)

        self._page.read_state(on_state)

    def shutdown(self) -> None:
        self.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)

    # ----- internals -----

    def _emit(self, type_: EventType, **data) -> None:
        self.event.emit(BotEvent(type_, **data))

    def _set_status(self, status: BotStatus) -> None:
        self.status = status
        self.status_changed.emit(status)

    def _load_history(self, remaining: int, last_count: int, done: Callable[[], None]) -> None:
        """Scroll up until no more messages load (or the limit is hit), then scroll back down."""
        def on_state(state: ChatState) -> None:
            count = len(state.messages)
            if remaining <= 0 or count == last_count or not self.running:
                self._page.scroll_history(to_top=False)
                QTimer.singleShot(self._timing.settle_ms, done)
                return
            self._page.scroll_history(to_top=True)
            QTimer.singleShot(self._timing.scroll_wait_ms,
                              lambda: self._load_history(remaining - 1, count, done))

        self._page.read_state(on_state)

    def _finish_start(self, reply_to_pending: bool) -> None:
        def on_state(state: ChatState) -> None:
            if not self.running:
                return
            self._seen = state.incoming_ids()
            self._busy = False
            self._set_status(BotStatus.LISTENING)
            self._emit(EventType.HISTORY_LOADED, count=len(state.messages))
            self._poll_timer.start()
            if reply_to_pending and state.last_message_is_incoming:
                # Treat the unanswered trailing messages as new so they appear in the activity feed.
                for message in reversed(state.messages):
                    if not message.is_incoming:
                        break
                    self._seen.discard(message.id)
                self._emit(EventType.ANSWERING_PENDING)
                self._respond(force=True)

        self._page.read_state(on_state)

    def _poll(self) -> None:
        if not self.running or self._busy or self._debounce.isActive():
            return

        def on_state(state: ChatState) -> None:
            if not self.running:
                return
            if state.chat_id != self._chat_id:
                if not self._warned_chat_switch:
                    self._warned_chat_switch = True
                    self._emit(EventType.CHAT_SWITCHED)
                return
            if self._warned_chat_switch:
                self._warned_chat_switch = False
                self._emit(EventType.CHAT_RESTORED)
            if state.incoming_ids() - self._seen:
                self._debounce.start()

        self._page.read_state(on_state)

    def _respond(self, force: bool = False) -> None:
        if self._busy or (not self.running and not force):
            return
        self._busy = True

        def on_state(state: ChatState) -> None:
            for msg in state.messages:
                if msg.is_incoming and msg.id not in self._seen:
                    self._seen.add(msg.id)
                    self._emit(EventType.INCOMING, text=msg.text)
            if not state.messages:
                self._busy = False
                self._emit(EventType.NO_MESSAGES)
                return
            self._set_status(BotStatus.THINKING)
            self._executor.submit(self._generate, state.messages)

        self._page.read_state(on_state)

    def _generate(self, messages: Sequence[ChatMessage]) -> None:
        """Runs on the worker thread."""
        try:
            result: object = self._responder_factory().reply(messages)
        except AIError as e:
            result = e
        except Exception as e:  # never let the worker die silently
            log.exception("unexpected error while generating a reply")
            result = AIError(AIErrorKind.UNKNOWN, str(e))
        self._reply_ready.emit(result)

    def _on_reply_ready(self, result: object) -> None:
        self._busy = False
        self._set_status(BotStatus.LISTENING if self.running else BotStatus.OFF)
        if isinstance(result, AIError):
            # Show a repeated identical error only once.
            if str(result) != self._last_error:
                self._emit(EventType.AI_ERROR, error=result)
            self._last_error = str(result)
        elif not result:
            self._emit(EventType.NOTHING_TO_REPLY)
        else:
            self._last_error = ""
            self._page.send_message(result)
            self._emit(EventType.OUTGOING, text=result)
            self.replied.emit()
