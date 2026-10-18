"""Activity feed: bot events rendered as chat bubbles and status cards."""

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QWidget

from telegram_ai_bot.telegram.events import BotEvent
from telegram_ai_bot.ui import strings
from telegram_ai_bot.ui.strings import EventText, Tone
from telegram_ai_bot.ui.widgets import EmptyState, ScrollList, button, hbox, label, vbox

_CARD_STYLE = {
    Tone.SUCCESS: ("Success", "✅"),
    Tone.WARN: ("Warn", "⚠️"),
    Tone.ERROR: ("Error", "⛔"),
}


class ActivityView(QWidget):
    MAX_ITEMS = 300

    def __init__(self):
        super().__init__()
        self._list = ScrollList()
        self._empty = EmptyState("💬", strings.ACTIVITY_EMPTY_TITLE, strings.ACTIVITY_EMPTY_BODY)
        self._list.append(self._empty)

        self._typing = label("", "EvTyping")
        self._typing.hide()
        self._dots = 0
        self._typing_timer = QTimer(self, interval=400)
        self._typing_timer.timeout.connect(self._tick_typing)

        clear = button(strings.CLEAR, "Ghost")
        clear.clicked.connect(self.clear)
        footer = hbox()
        footer.addWidget(self._typing)
        footer.addStretch()
        footer.addWidget(clear)

        layout = vbox(self, spacing=4)
        layout.addWidget(self._list, 1)
        layout.addLayout(footer)

    # ----- public -----

    def add_event(self, event: BotEvent) -> None:
        self.add(strings.describe_event(event))

    def add(self, text: EventText) -> None:
        if self._empty is not None:
            self._list.clear()
            self._empty = None
        self._list.append(self._build(text))
        while self._list.count() > self.MAX_ITEMS:
            old = self._list.items.takeAt(0).widget()
            if old:
                old.deleteLater()
        QTimer.singleShot(30, self._list.scroll_to_bottom)

    def clear(self) -> None:
        self._list.clear()
        self._empty = EmptyState("💬", strings.ACTIVITY_EMPTY_TITLE, strings.ACTIVITY_EMPTY_BODY)
        self._list.append(self._empty)

    def set_typing(self, on: bool) -> None:
        self._typing.setVisible(on)
        if on:
            self._tick_typing()
            self._typing_timer.start()
        else:
            self._typing_timer.stop()

    # ----- rendering -----

    def _tick_typing(self) -> None:
        self._dots = (self._dots + 1) % 4
        self._typing.setText(strings.TYPING + "." * self._dots)

    def _build(self, text: EventText) -> QWidget:
        now = time.strftime("%H:%M")
        if text.tone in (Tone.INCOMING, Tone.OUTGOING):
            return self._bubble(text, now)
        if text.tone is Tone.INFO:
            row = QWidget()
            layout = hbox(row)
            layout.addWidget(label(text.title, "EvInfo", True), 1)
            layout.addWidget(label(now, "EvTime"), 0, Qt.AlignTop)
            return row
        return self._card(text, now)

    @staticmethod
    def _bubble(text: EventText, now: str) -> QWidget:
        incoming = text.tone is Tone.INCOMING
        bubble = QFrame()
        bubble.setObjectName("EvBubbleIn" if incoming else "EvBubbleOut")
        layout = vbox(bubble, (12, 8, 12, 8), 2)
        head = hbox()
        head.addWidget(label(strings.INCOMING_LABEL if incoming else strings.OUTGOING_LABEL, "EvBubbleLabel"))
        head.addStretch()
        head.addWidget(label(now, "EvTime"))
        body = label(text.title, "EvBubbleText", True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addLayout(head)
        layout.addWidget(body)

        # Incoming on the leading (right) side, bot replies on the trailing (left) side.
        row = QWidget()
        row_layout = hbox(row)
        if incoming:
            row_layout.addWidget(bubble, 5)
            row_layout.addStretch(1)
        else:
            row_layout.addStretch(1)
            row_layout.addWidget(bubble, 5)
        return row

    @staticmethod
    def _card(text: EventText, now: str) -> QWidget:
        name, icon = _CARD_STYLE[text.tone]
        card = QFrame()
        card.setObjectName(f"Ev{name}")
        layout = vbox(card, (12, 10, 12, 10), 4)
        head = hbox()
        head.addWidget(label(f"{icon}  {text.title}", f"EvTitle{name}", True), 1)
        head.addWidget(label(now, "EvTime"), 0, Qt.AlignTop)
        layout.addLayout(head)
        if text.hint:
            layout.addWidget(label(text.hint, "EvHint", True))
        if text.detail:
            detail = label(text.detail, "Hint", True)
            detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
            detail.setLayoutDirection(Qt.LeftToRight)
            detail.hide()
            toggle = button(strings.TECHNICAL_DETAILS, "Ghost")
            toggle.clicked.connect(lambda: detail.setVisible(not detail.isVisible()))
            toggle_row = hbox()
            toggle_row.addWidget(toggle)
            toggle_row.addStretch()
            layout.addLayout(toggle_row)
            layout.addWidget(detail)
        return card
