import pytest

from telegram_ai_bot.ai.errors import AIError, AIErrorKind
from telegram_ai_bot.telegram.bot import BotController, BotTiming
from telegram_ai_bot.telegram.events import BotStatus, EventType

from .conftest import FakeTelegramPage, msg, wait_until

FAST = BotTiming(poll_ms=20, debounce_ms=60, history_scrolls=3, scroll_wait_ms=10, settle_ms=10)


class RecordingResponder:
    def __init__(self, replies=None, error: AIError | None = None):
        self.calls: list[list] = []
        self._replies = replies
        self._error = error

    def __call__(self):  # used as the responder factory
        return self

    def reply(self, messages):
        self.calls.append(list(messages))
        if self._error:
            raise self._error
        return self._replies(len(self.calls)) if self._replies else f"reply {len(self.calls)}"


@pytest.fixture
def make_bot(qapp):
    bots = []

    def factory(page, responder):
        bot = BotController(page, responder, timing=FAST)
        events = []
        bot.event.connect(events.append)
        bots.append(bot)
        return bot, events

    yield factory
    for bot in bots:
        bot.shutdown()


def types(events):
    return [e.type for e in events]


def test_start_requires_login(make_bot):
    bot, events = make_bot(FakeTelegramPage(logged_in=False), RecordingResponder())
    bot.start(reply_to_pending=True)
    wait_until(lambda: events)
    assert types(events) == [EventType.NOT_LOGGED_IN]
    assert not bot.running


def test_start_requires_open_chat(make_bot):
    bot, events = make_bot(FakeTelegramPage(title=""), RecordingResponder())
    bot.start(reply_to_pending=True)
    wait_until(lambda: events)
    assert types(events) == [EventType.NO_CHAT_OPEN]


def test_answers_pending_then_batches_new_messages(make_bot):
    page = FakeTelegramPage([msg("1", "hi", incoming=False), msg("2", "are you coming tomorrow?")])
    responder = RecordingResponder()
    bot, events = make_bot(page, responder)

    bot.start(reply_to_pending=True)
    wait_until(lambda: page.sent == ["reply 1"])
    assert bot.status is BotStatus.LISTENING

    page.receive("what time?")
    page.receive("answer please")
    wait_until(lambda: len(page.sent) == 2)

    assert len(responder.calls) == 2  # two quick messages -> a single reply
    assert [m.text for m in responder.calls[1]][-2:] == ["what time?", "answer please"]
    incoming = [e.text for e in events if e.type is EventType.INCOMING]
    assert incoming == ["are you coming tomorrow?", "what time?", "answer please"]


def test_does_not_answer_pending_when_disabled(make_bot):
    page = FakeTelegramPage([msg("1", "old question")])
    responder = RecordingResponder()
    bot, events = make_bot(page, responder)
    bot.start(reply_to_pending=False)
    wait_until(lambda: EventType.HISTORY_LOADED in types(events))
    page.receive("new question")
    wait_until(lambda: page.sent)
    assert len(responder.calls) == 1
    assert [e.text for e in events if e.type is EventType.INCOMING] == ["new question"]


def test_loads_older_history_by_scrolling(make_bot):
    page = FakeTelegramPage([msg("3", "recent")], older=[msg("1", "older"), msg("2", "old", incoming=False)])
    bot, events = make_bot(page, RecordingResponder())
    bot.start(reply_to_pending=False)
    wait_until(lambda: EventType.HISTORY_LOADED in types(events))
    loaded = next(e for e in events if e.type is EventType.HISTORY_LOADED)
    assert loaded.count == 3
    assert page.scrolls[0] is True and page.scrolls[-1] is False  # up first, back down at the end


def test_stop_prevents_replies(make_bot):
    page = FakeTelegramPage([msg("1", "hello", incoming=False)])
    responder = RecordingResponder()
    bot, events = make_bot(page, responder)
    bot.start(reply_to_pending=True)
    wait_until(lambda: bot.status is BotStatus.LISTENING)
    bot.stop()
    page.receive("anyone there?")
    for _ in range(20):
        wait_until(lambda: True)
    assert responder.calls == []
    assert EventType.STOPPED in types(events)


def test_warns_once_on_chat_switch_and_recovers(make_bot):
    page = FakeTelegramPage([msg("1", "hello", incoming=False)])
    bot, events = make_bot(page, RecordingResponder())
    bot.start(reply_to_pending=False)
    wait_until(lambda: bot.status is BotStatus.LISTENING)

    page.chat_id = "#@someone-else"
    wait_until(lambda: EventType.CHAT_SWITCHED in types(events))
    page.chat_id = "#@ali"
    wait_until(lambda: EventType.CHAT_RESTORED in types(events))
    assert types(events).count(EventType.CHAT_SWITCHED) == 1


def test_repeated_identical_errors_are_reported_once(make_bot):
    page = FakeTelegramPage([msg("1", "q1")])
    responder = RecordingResponder(error=AIError(AIErrorKind.REGION_BLOCKED, "blocked"))
    bot, events = make_bot(page, responder)
    bot.start(reply_to_pending=True)
    wait_until(lambda: len(responder.calls) == 1 and bot.status is BotStatus.LISTENING)
    page.receive("q2")
    wait_until(lambda: len(responder.calls) == 2 and bot.status is BotStatus.LISTENING)

    errors = [e for e in events if e.type is EventType.AI_ERROR]
    assert len(errors) == 1
    assert errors[0].error.kind is AIErrorKind.REGION_BLOCKED
    assert page.sent == []


def test_reply_now_works_while_stopped(make_bot):
    page = FakeTelegramPage([msg("1", "price?")])
    bot, events = make_bot(page, RecordingResponder())
    bot.reply_now()
    wait_until(lambda: page.sent == ["reply 1"])
    assert not bot.running
    assert bot.status is BotStatus.OFF


def test_unexpected_exception_becomes_ai_error(make_bot):
    class Broken:
        def reply(self, messages):
            raise ValueError("boom")

    page = FakeTelegramPage([msg("1", "hi")])
    bot, events = make_bot(page, lambda: Broken())
    bot.reply_now()
    wait_until(lambda: EventType.AI_ERROR in types(events))
    error = next(e for e in events if e.type is EventType.AI_ERROR).error
    assert error.kind is AIErrorKind.UNKNOWN
