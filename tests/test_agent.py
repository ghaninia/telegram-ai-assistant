from datetime import datetime

import pytest

from telegram_ai_bot.ai.agent import MEDIA_PLACEHOLDER, ReplyAgent, build_contents, build_system_prompt
from telegram_ai_bot.ai.errors import AIError, AIErrorKind
from telegram_ai_bot.core.models import KnowledgeItem
from telegram_ai_bot.storage.settings import AppSettings

from .conftest import msg


def test_build_contents_merges_consecutive_messages_and_drops_leading_model_turns():
    contents = build_contents([
        msg("1", "hello", incoming=False),
        msg("2", "hi"),
        msg("3", "are you there?"),
        msg("4", "yes", incoming=False),
        msg("5", ""),
    ])
    assert contents == [
        {"role": "user", "parts": [{"text": "hi\nare you there?"}]},
        {"role": "model", "parts": [{"text": "yes"}]},
        {"role": "user", "parts": [{"text": MEDIA_PLACEHOLDER}]},
    ]


def test_build_contents_respects_limit():
    messages = [msg(str(i), f"m{i}", incoming=i % 2 == 0) for i in range(10)]
    contents = build_contents(messages, limit=3)
    assert [c["parts"][0]["text"] for c in contents] == ["m8", "m9"]  # "m7" (model) dropped as leading


def test_system_prompt_contains_date_and_enabled_knowledge():
    knowledge = [KnowledgeItem(1, "Hours", "9 to 6", True)]
    prompt = build_system_prompt("BASE", knowledge, now=datetime(2026, 10, 19, 10, 30))
    assert prompt.startswith("BASE")
    assert "Monday, 2026-10-19 10:30 (Jalali 1405/07/27)" in prompt
    assert "## Hours\n9 to 6" in prompt


def test_system_prompt_without_knowledge_has_no_knowledge_section():
    assert "# Knowledge" not in build_system_prompt("BASE", [])


class FakeClient:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.models: list[str] = []

    def __call__(self, **_kwargs):  # used as client_factory
        return self

    def generate(self, model, system, contents):
        self.models.append(model)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


SETTINGS = AppSettings(api_key="k", model="primary", fallback_models=("backup-1", "backup-2"))


def test_falls_back_to_next_model_on_retryable_error():
    client = FakeClient([AIError(AIErrorKind.RATE_LIMITED), "hello!"])
    reply = ReplyAgent(SETTINGS, [], client_factory=client).reply([msg("1", "hi")])
    assert reply == "hello!"
    assert client.models == ["primary", "backup-1"]


def test_stops_on_non_retryable_error():
    client = FakeClient([AIError(AIErrorKind.INVALID_API_KEY), "unused"])
    with pytest.raises(AIError) as excinfo:
        ReplyAgent(SETTINGS, [], client_factory=client).reply([msg("1", "hi")])
    assert excinfo.value.kind is AIErrorKind.INVALID_API_KEY
    assert client.models == ["primary"]


def test_raises_last_error_when_all_models_fail():
    client = FakeClient([AIError(AIErrorKind.SERVER_ERROR)] * 3)
    with pytest.raises(AIError) as excinfo:
        ReplyAgent(SETTINGS, [], client_factory=client).reply([msg("1", "hi")])
    assert excinfo.value.kind is AIErrorKind.SERVER_ERROR
    assert client.models == ["primary", "backup-1", "backup-2"]


def test_returns_none_when_last_message_is_ours():
    client = FakeClient([])
    assert ReplyAgent(SETTINGS, [], client_factory=client).reply([msg("1", "hi"), msg("2", "ok", False)]) is None
    assert client.models == []
