import json
from datetime import datetime

import pytest

from telegram_ai_bot.ai.errors import AIError, AIErrorKind
from telegram_ai_bot.core.calendar import describe_now, to_jalali
from telegram_ai_bot.core.models import ChatState, Direction
from telegram_ai_bot.telegram.events import BotEvent, EventType
from telegram_ai_bot.ui import strings


@pytest.mark.parametrize(("gregorian", "jalali"), [
    ((2025, 3, 21), (1404, 1, 1)),  # Nowruz
    ((2026, 10, 19), (1405, 7, 27)),
    ((2024, 3, 20), (1403, 1, 1)),
    ((2023, 12, 31), (1402, 10, 10)),
])
def test_to_jalali(gregorian, jalali):
    assert to_jalali(*gregorian) == jalali


def test_describe_now():
    assert describe_now(datetime(2025, 3, 21, 8, 5)) == "Friday, 2025-03-21 08:05 (Jalali 1404/01/01)"


def test_chat_state_from_json():
    raw = json.dumps({"loggedIn": True, "chatId": "#@ali", "title": "Ali",
                      "history": [["1", "out", "hi"], ["2", "in", "hello"]]})
    state = ChatState.from_json(raw)
    assert state.logged_in and state.has_open_chat
    assert [m.direction for m in state.messages] == [Direction.OUTGOING, Direction.INCOMING]
    assert state.incoming_ids() == {"2"}
    assert state.last_message_is_incoming


@pytest.mark.parametrize("raw", [None, "", "not json", "[1, 2]", '{"history": [["1", "sideways", "x"]]}'])
def test_chat_state_from_bad_json_is_empty(raw):
    assert ChatState.from_json(raw) == ChatState()


def test_every_ai_error_kind_has_a_message():
    assert set(strings.AI_ERRORS) == set(AIErrorKind)


def test_every_event_type_has_a_description():
    error = AIError(AIErrorKind.NETWORK_ERROR, "down")
    for event_type in EventType:
        text = strings.describe_event(BotEvent(event_type, text="x", count=1, error=error))
        assert text.title and text.title != event_type.name
