"""Typed AI errors. The UI maps each kind to a user-friendly message."""

from enum import Enum, auto


class AIErrorKind(Enum):
    MISSING_API_KEY = auto()
    REGION_BLOCKED = auto()  # Google refuses requests from this country (e.g. Iran)
    INVALID_API_KEY = auto()
    PERMISSION_DENIED = auto()
    MODEL_NOT_FOUND = auto()
    RATE_LIMITED = auto()
    SERVER_ERROR = auto()
    NETWORK_ERROR = auto()
    EMPTY_RESPONSE = auto()  # e.g. blocked by safety filters
    UNKNOWN = auto()


# Errors where trying the next fallback model may help.
FALLBACK_WORTHY = frozenset({
    AIErrorKind.MODEL_NOT_FOUND,
    AIErrorKind.RATE_LIMITED,
    AIErrorKind.SERVER_ERROR,
    AIErrorKind.EMPTY_RESPONSE,
    AIErrorKind.UNKNOWN,
})


class AIError(Exception):
    def __init__(self, kind: AIErrorKind, detail: str = "", model: str = ""):
        self.kind = kind
        self.detail = detail
        self.model = model
        super().__init__(f"{kind.name}{f' [{model}]' if model else ''}: {detail}")
