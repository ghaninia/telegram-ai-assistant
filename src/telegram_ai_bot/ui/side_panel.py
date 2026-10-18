"""Left-hand control panel: status, controls, activity feed and knowledge base."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QPushButton, QStackedWidget

from telegram_ai_bot import config
from telegram_ai_bot.paths import RESOURCES_DIR
from telegram_ai_bot.storage.knowledge import KnowledgeRepository
from telegram_ai_bot.telegram.bot import BotController
from telegram_ai_bot.telegram.events import BotEvent, BotStatus
from telegram_ai_bot.ui import strings
from telegram_ai_bot.ui.activity_view import ActivityView
from telegram_ai_bot.ui.knowledge_view import KnowledgeView
from telegram_ai_bot.ui.strings import Tone
from telegram_ai_bot.ui.theme import C
from telegram_ai_bot.ui.widgets import Switch, button, hbox, label, vbox

STATUS_COLORS = {
    BotStatus.OFF: C["faint"],
    BotStatus.LOADING: C["warn"],
    BotStatus.LISTENING: C["success"],
    BotStatus.THINKING: C["primary"],
}


class SidePanel(QFrame):
    settings_requested = Signal()
    reload_requested = Signal()

    def __init__(self, bot: BotController, knowledge_repo: KnowledgeRepository):
        super().__init__()
        self.setObjectName("SidePanel")
        self._bot = bot
        self._knowledge_repo = knowledge_repo
        self._replies = 0

        self.activity = ActivityView()
        self.knowledge = KnowledgeView(knowledge_repo)

        layout = vbox(self, (18, 18, 18, 14), 12)
        layout.addLayout(self._build_header())
        layout.addWidget(self._build_status_card())
        layout.addLayout(self._build_controls())
        layout.addSpacing(2)
        layout.addWidget(self._build_tabs())
        layout.addWidget(self._stack, 1)

        bot.event.connect(self._on_event)
        bot.status_changed.connect(self._on_status)
        bot.chat_changed.connect(lambda name: self._status_sub.setText(strings.CHAT_LABEL.format(name=name)))
        bot.replied.connect(self._on_replied)
        self.knowledge.changed.connect(self._refresh_knowledge_count)
        self._on_status(BotStatus.OFF)
        self._refresh_knowledge_count()

    # ----- construction -----

    def _build_header(self):
        logo = QLabel()
        logo.setPixmap(QPixmap(str(RESOURCES_DIR / "icon.png")).scaled(
            40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        titles = vbox(spacing=0)
        titles.addWidget(label(strings.APP_TITLE, "AppTitle"))
        titles.addWidget(label(strings.APP_SUBTITLE, "AppSubtitle"))
        settings = button("⚙️", "IconButton", strings.SETTINGS_TIP)
        settings.clicked.connect(self.settings_requested)

        header = hbox(spacing=10)
        header.addWidget(logo)
        header.addLayout(titles, 1)
        header.addWidget(settings)
        return header

    def _build_status_card(self) -> QFrame:
        self._dot = QLabel()
        self._dot.setFixedSize(10, 10)
        self._status_text = label("", "StatusText")
        self._status_sub = label(strings.NO_CHAT_SELECTED, "StatusSub", True)
        head = hbox(spacing=8)
        head.addWidget(self._dot, 0, Qt.AlignVCenter)
        head.addWidget(self._status_text, 1)

        self._stat_replies = label("0", "StatValue")
        self._stat_knowledge = label("0", "StatValue")
        stats = hbox(spacing=8)
        for value, caption in ((self._stat_replies, strings.STAT_REPLIES),
                               (self._stat_knowledge, strings.STAT_KNOWLEDGE)):
            tile = QFrame()
            tile.setObjectName("Card")
            tile_layout = vbox(tile, (12, 8, 12, 8), 0)
            for widget in (value, label(caption, "StatLabel")):
                # Digits would otherwise be aligned as left-to-right text.
                widget.setAlignment(Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter)
                tile_layout.addWidget(widget)
            stats.addWidget(tile, 1)

        card = QFrame()
        card.setObjectName("StatusCard")
        card_layout = vbox(card, (14, 12, 14, 12), 6)
        card_layout.addLayout(head)
        card_layout.addWidget(self._status_sub)
        card_layout.addSpacing(4)
        card_layout.addLayout(stats)
        return card

    def _build_controls(self):
        self._toggle = QPushButton()
        self._toggle.setCursor(Qt.PointingHandCursor)
        self._toggle.clicked.connect(self._toggle_bot)

        reply_now = button(strings.REPLY_NOW, tooltip=strings.REPLY_NOW_TIP)
        reply_now.clicked.connect(self._bot.reply_now)
        reload = button(strings.RELOAD, tooltip=strings.RELOAD_TIP)
        reload.clicked.connect(self.reload_requested)
        secondary = hbox()
        secondary.addWidget(reply_now, 1)
        secondary.addWidget(reload, 1)

        self._reply_to_pending = Switch(checked=config.REPLY_TO_PENDING_DEFAULT)
        pending = hbox()
        pending.addWidget(self._reply_to_pending)
        pending.addWidget(label(strings.REPLY_TO_PENDING, "Hint", True), 1)

        controls = vbox(spacing=12)
        controls.addWidget(self._toggle)
        controls.addLayout(secondary)
        controls.addLayout(pending)
        return controls

    def _build_tabs(self) -> QFrame:
        self._stack = QStackedWidget()
        self._stack.addWidget(self.activity)
        self._stack.addWidget(self.knowledge)

        segment = QFrame()
        segment.setObjectName("Segment")
        segment_layout = hbox(segment, (3, 3, 3, 3), 3)
        self._tab_activity = button(strings.TAB_ACTIVITY)
        self._tab_knowledge = button(strings.TAB_KNOWLEDGE)
        group = QButtonGroup(self)
        for index, tab in enumerate((self._tab_activity, self._tab_knowledge)):
            tab.setCheckable(True)
            group.addButton(tab, index)
            segment_layout.addWidget(tab, 1)
        self._tab_activity.setChecked(True)
        group.idClicked.connect(self._stack.setCurrentIndex)
        return segment

    # ----- behaviour -----

    def show_activity(self) -> None:
        self._tab_activity.click()

    def _toggle_bot(self) -> None:
        if self._bot.running:
            self._bot.stop()
        else:
            self.show_activity()
            self._bot.start(self._reply_to_pending.isChecked())

    def _on_status(self, status: BotStatus) -> None:
        self._status_text.setText(strings.STATUS_LABELS[status])
        self._dot.setStyleSheet(f"background: {STATUS_COLORS[status]}; border-radius: 5px;")
        self.activity.set_typing(status is BotStatus.THINKING)
        running = self._bot.running
        self._toggle.setObjectName("Danger" if running else "Primary")
        self._toggle.setText(strings.STOP if running else strings.START)
        self._toggle.setEnabled(status is not BotStatus.LOADING)
        # Re-apply the stylesheet after changing objectName.
        self._toggle.style().unpolish(self._toggle)
        self._toggle.style().polish(self._toggle)

    def _on_event(self, event: BotEvent) -> None:
        self.activity.add_event(event)
        if strings.describe_event(event).tone in (Tone.ERROR, Tone.WARN):
            self.show_activity()

    def _on_replied(self) -> None:
        self._replies += 1
        self._stat_replies.setText(str(self._replies))

    def _refresh_knowledge_count(self) -> None:
        count = self._knowledge_repo.count_enabled()
        self._stat_knowledge.setText(str(count))
        self._tab_knowledge.setText(strings.TAB_KNOWLEDGE_COUNT.format(count=count) if count else strings.TAB_KNOWLEDGE)
