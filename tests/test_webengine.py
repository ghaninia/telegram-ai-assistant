"""Runs the real page scripts inside Qt WebEngine against a minimal copy of Telegram Web's markup.

Needs a display: RUN_GUI_TESTS=1 pytest -m gui
"""

import os

import pytest

from telegram_ai_bot.core.models import Direction
from telegram_ai_bot.telegram.bot import BotController, BotTiming
from telegram_ai_bot.telegram.events import EventType

from .conftest import wait_until

pytestmark = [
    pytest.mark.gui,
    pytest.mark.skipif(not os.environ.get("RUN_GUI_TESTS"), reason="set RUN_GUI_TESTS=1 to run"),
]

FAKE_TELEGRAM = """<html><body>
<div id="column-left"><div class="chatlist"></div></div>
<div id="column-center">
  <div class="chat-info"><span class="peer-title">Ali</span></div>
  <div class="bubbles"><div class="scrollable"><div class="bubbles-inner">
    <div class="bubble service" data-mid="0"><div class="message">Today</div></div>
    <div class="bubble is-out" data-mid="1"><div class="message">
      <span class="translatable-message">سلام</span><span class="time">10:00</span></div></div>
    <div class="bubble is-in" data-mid="2"><div class="message">
      <span class="translatable-message">فردا میای؟</span><span class="time">10:01</span></div></div>
  </div></div></div>
  <div class="input-message-input" contenteditable="true"></div>
  <button class="btn-send">send</button>
</div>
<script>
let next = 100;
function addBubble(cls, text) {
  const b = document.createElement('div');
  b.className = 'bubble ' + cls; b.dataset.mid = String(next++);
  b.innerHTML = '<div class="message"><span class="translatable-message"></span></div>';
  b.querySelector('span').innerText = text;
  document.querySelector('.bubbles-inner').appendChild(b);
}
document.querySelector('.btn-send').onclick = () => {
  const box = document.querySelector('.input-message-input');
  addBubble('is-out', box.innerText); box.innerHTML = '';
};
window.incoming = (text) => addBubble('is-in', text);
</script></body></html>"""


@pytest.fixture
def telegram_page(qapp):
    from PySide6.QtWebEngineWidgets import QWebEngineView

    from telegram_ai_bot.telegram.page import WebEngineTelegramPage

    view = QWebEngineView()
    loaded = []
    view.loadFinished.connect(loaded.append)
    view.setHtml(FAKE_TELEGRAM)
    wait_until(lambda: loaded, timeout=20)
    yield view, WebEngineTelegramPage(view.page())
    view.deleteLater()
    qapp.processEvents()


def test_state_script_reads_chat(telegram_page):
    _, page = telegram_page
    states = []
    page.read_state(states.append)
    wait_until(lambda: states)
    state = states[0]
    assert state.logged_in and state.title == "Ali"
    assert [(m.id, m.direction, m.text) for m in state.messages] == [
        ("1", Direction.OUTGOING, "سلام"),
        ("2", Direction.INCOMING, "فردا میای؟"),  # service bubble and time stamp excluded
    ]


def test_bot_end_to_end_on_real_page(telegram_page):
    view, page = telegram_page
    calls = []

    class Responder:
        def reply(self, messages):
            calls.append(messages)
            return f"جواب {len(calls)} 😀"

    bot = BotController(page, Responder, BotTiming(poll_ms=100, debounce_ms=300, history_scrolls=1,
                                                   scroll_wait_ms=50, settle_ms=50))
    events = []
    bot.event.connect(events.append)
    bot.start(reply_to_pending=True)
    wait_until(lambda: [e for e in events if e.type is EventType.OUTGOING], timeout=10)

    view.page().runJavaScript("incoming('ساعت چند؟'); incoming('جواب بده');")
    wait_until(lambda: len([e for e in events if e.type is EventType.OUTGOING]) == 2, timeout=10)

    # The send script clicks "send" after a short delay, so poll the page until the reply appears.
    texts = []

    def reply_visible() -> bool:
        page.read_state(lambda st: texts.__setitem__(slice(None), [(m.direction.value, m.text) for m in st.messages]))
        return bool(texts) and texts[-1] == ("out", "جواب 2 😀")

    wait_until(reply_visible, timeout=10)
    assert texts[-3:] == [("in", "ساعت چند؟"), ("in", "جواب بده"), ("out", "جواب 2 😀")]
    assert len(calls) == 2
    bot.shutdown()
