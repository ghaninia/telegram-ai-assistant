"""Domain models shared across the app."""

import json
from dataclasses import dataclass, field
from enum import StrEnum


class Direction(StrEnum):
    INCOMING = "in"  # written by the other person
    OUTGOING = "out"  # written from this account (by the user or the bot)


@dataclass(frozen=True, slots=True)
class ChatMessage:
    id: str
    direction: Direction
    text: str

    @property
    def is_incoming(self) -> bool:
        return self.direction is Direction.INCOMING


@dataclass(frozen=True, slots=True)
class ChatState:
    """Snapshot of the Telegram page: login state, open chat and its loaded messages."""

    logged_in: bool = False
    chat_id: str = ""
    title: str = ""
    messages: tuple[ChatMessage, ...] = field(default_factory=tuple)

    @property
    def has_open_chat(self) -> bool:
        return bool(self.title)

    @property
    def last_message_is_incoming(self) -> bool:
        return bool(self.messages) and self.messages[-1].is_incoming

    def incoming_ids(self) -> set[str]:
        return {m.id for m in self.messages if m.is_incoming}

    @classmethod
    def from_json(cls, raw: str | None) -> "ChatState":
        """Parse the JSON produced by telegram.scripts.STATE_SCRIPT; tolerate garbage."""
        if not raw:
            return cls()
        try:
            data = json.loads(raw)
            messages = tuple(
                ChatMessage(id=str(mid), direction=Direction(direction), text=text or "")
                for mid, direction, text in data.get("history", [])
            )
            return cls(
                logged_in=bool(data.get("loggedIn")),
                chat_id=data.get("chatId", ""),
                title=data.get("title", ""),
                messages=messages,
            )
        except (ValueError, TypeError, AttributeError):
            return cls()


@dataclass(frozen=True, slots=True)
class KnowledgeItem:
    id: int
    title: str
    content: str
    enabled: bool
    created_at: str = ""
    updated_at: str = ""
