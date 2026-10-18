"""Events and states emitted by the bot. They carry data only; the UI decides how to present them."""

from dataclasses import dataclass
from enum import Enum, auto

from telegram_ai_bot.ai.errors import AIError


class BotStatus(Enum):
    OFF = auto()
    LOADING = auto()  # reading history after start
    LISTENING = auto()
    THINKING = auto()  # waiting for the model


class EventType(Enum):
    STARTED = auto()  # text = chat title
    HISTORY_LOADED = auto()  # count = messages read
    ANSWERING_PENDING = auto()
    STOPPED = auto()
    BUSY = auto()
    NOT_LOGGED_IN = auto()
    NO_CHAT_OPEN = auto()
    CHAT_SWITCHED = auto()
    CHAT_RESTORED = auto()
    NO_MESSAGES = auto()
    INCOMING = auto()  # text = message
    OUTGOING = auto()  # text = reply sent
    NOTHING_TO_REPLY = auto()
    AI_ERROR = auto()  # error = AIError
    PAGE_LOAD_FAILED = auto()


@dataclass(frozen=True, slots=True)
class BotEvent:
    type: EventType
    text: str = ""
    count: int = 0
    error: AIError | None = None
