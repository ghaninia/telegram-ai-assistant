"""Widget smoke tests (headless). The Telegram web view itself is not created here."""

from telegram_ai_bot.ai.errors import AIError, AIErrorKind
from telegram_ai_bot.storage.knowledge import KnowledgeRepository
from telegram_ai_bot.telegram.bot import BotController
from telegram_ai_bot.telegram.events import BotEvent, BotStatus, EventType
from telegram_ai_bot.ui import strings
from telegram_ai_bot.ui.activity_view import ActivityView
from telegram_ai_bot.ui.knowledge_view import KnowledgeView
from telegram_ai_bot.ui.side_panel import SidePanel

from .conftest import FakeTelegramPage


def test_activity_view_renders_every_event(qapp):
    view = ActivityView()
    error = AIError(AIErrorKind.REGION_BLOCKED, "blocked")
    for event_type in EventType:
        view.add_event(BotEvent(event_type, text="متن", count=3, error=error))
    assert view._list.count() == len(EventType)
    view.clear()
    assert view._list.count() == 1  # empty state


def test_knowledge_view_reflects_repository(qapp, db):
    repo = KnowledgeRepository(db)
    view = KnowledgeView(repo)
    assert view._list.count() == 1  # empty state
    repo.add("ساعت کاری", "۹ تا ۶")
    repo.add("آدرس", "تهران")
    view.reload()
    assert view._list.count() == 2
    view._search.setText("تهران")
    assert view._list.count() == 1


def test_side_panel_tracks_bot_state(qapp, db):
    repo = KnowledgeRepository(db)
    repo.add("a", "b")
    bot = BotController(FakeTelegramPage(), lambda: None)
    panel = SidePanel(bot, repo)
    assert panel._stat_knowledge.text() == "1"
    assert panel._toggle.text() == strings.START

    bot.running = True
    bot.status_changed.emit(BotStatus.LISTENING)
    assert panel._toggle.text() == strings.STOP
    assert panel._status_text.text() == strings.STATUS_LABELS[BotStatus.LISTENING]

    bot.replied.emit()
    assert panel._stat_replies.text() == "1"
    bot.shutdown()
