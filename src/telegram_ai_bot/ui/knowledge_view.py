"""Knowledge base list, cards and edit dialog."""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QDialog, QFrame, QLineEdit, QMessageBox, QPlainTextEdit, QWidget

from telegram_ai_bot.core.models import KnowledgeItem
from telegram_ai_bot.storage.knowledge import KnowledgeRepository
from telegram_ai_bot.ui import strings
from telegram_ai_bot.ui.theme import C
from telegram_ai_bot.ui.widgets import EmptyState, ScrollList, Switch, button, hbox, label, vbox

PREVIEW_CHARS = 110


class KnowledgeDialog(QDialog):
    def __init__(self, repo: KnowledgeRepository, item: KnowledgeItem | None, parent: QWidget | None = None):
        super().__init__(parent)
        self._repo = repo
        self._item = item
        self.setWindowTitle(strings.KNOWLEDGE_DIALOG_EDIT if item else strings.KNOWLEDGE_DIALOG_ADD)
        self.setMinimumSize(520, 460)

        self._title = QLineEdit(item.title if item else "")
        self._title.setPlaceholderText(strings.TITLE_PLACEHOLDER)
        self._content = QPlainTextEdit(item.content if item else "")
        self._content.setPlaceholderText(strings.CONTENT_PLACEHOLDER)
        self._enabled = Switch(checked=item.enabled if item else True)

        enabled_row = hbox()
        enabled_row.addWidget(self._enabled)
        enabled_row.addWidget(label(strings.KNOWLEDGE_ENABLED))
        enabled_row.addStretch()

        save = button(strings.SAVE, "Primary")
        save.clicked.connect(self._save)
        cancel = button(strings.CANCEL)
        cancel.clicked.connect(self.reject)
        footer = hbox()
        if item:
            delete = button(strings.DELETE, "DangerText")
            delete.clicked.connect(self._delete)
            footer.addWidget(delete)
        footer.addStretch()
        footer.addWidget(cancel)
        footer.addWidget(save)

        layout = vbox(self, (20, 20, 20, 20), 8)
        layout.addWidget(label(strings.FIELD_TITLE, "FieldLabel"))
        layout.addWidget(self._title)
        layout.addSpacing(4)
        layout.addWidget(label(strings.FIELD_CONTENT, "FieldLabel"))
        layout.addWidget(self._content, 1)
        layout.addLayout(enabled_row)
        layout.addSpacing(6)
        layout.addLayout(footer)

    def _save(self) -> None:
        title, content = self._title.text().strip(), self._content.toPlainText().strip()
        if not title or not content:
            QMessageBox.warning(self, strings.INCOMPLETE_TITLE, strings.INCOMPLETE_BODY)
            return
        if self._item:
            self._repo.update(self._item.id, title, content, self._enabled.isChecked())
        else:
            self._repo.add(title, content, self._enabled.isChecked())
        self.accept()

    def _delete(self) -> None:
        answer = QMessageBox.question(self, strings.DELETE_TITLE, strings.DELETE_CONFIRM.format(title=self._item.title))
        if answer == QMessageBox.Yes:
            self._repo.delete(self._item.id)
            self.accept()


class KnowledgeCard(QFrame):
    clicked = Signal(int)
    toggled = Signal(int, bool)

    def __init__(self, item: KnowledgeItem):
        super().__init__()
        self.setObjectName("KnowledgeCard")
        self.setAttribute(Qt.WA_Hover)
        self.setCursor(Qt.PointingHandCursor)
        self._id = item.id

        preview = " ".join(item.content.split())
        if len(preview) > PREVIEW_CHARS:
            preview = preview[:PREVIEW_CHARS] + "…"
        title = label(item.title, "CardTitle", True)
        body = label(preview, "CardBody", True)
        if not item.enabled:
            for widget in (title, body):
                widget.setStyleSheet(f"color: {C['faint']};")

        switch = Switch(checked=item.enabled)
        switch.setToolTip(strings.KNOWLEDGE_TOGGLE_TIP)
        switch.toggled.connect(lambda on: self.toggled.emit(self._id, on))

        text = vbox(spacing=2)
        text.addWidget(title)
        text.addWidget(body)
        layout = hbox(self, (14, 12, 14, 12), 12)
        layout.addLayout(text, 1)
        layout.addWidget(switch, 0, Qt.AlignTop)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._id)
        super().mouseReleaseEvent(event)


class KnowledgeView(QWidget):
    changed = Signal()  # items added, edited, deleted or toggled

    def __init__(self, repo: KnowledgeRepository):
        super().__init__()
        self._repo = repo

        self._search = QLineEdit()
        self._search.setPlaceholderText(strings.KNOWLEDGE_SEARCH)
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self.reload)
        add = button(strings.KNOWLEDGE_ADD)
        add.clicked.connect(lambda: self._open(None))
        top = hbox()
        top.addWidget(self._search, 1)
        top.addWidget(add)

        self._list = ScrollList()
        layout = vbox(self, spacing=8)
        layout.addLayout(top)
        layout.addWidget(label(strings.KNOWLEDGE_HINT, "Hint", True))
        layout.addWidget(self._list, 1)
        self.reload()

    def reload(self) -> None:
        self._list.clear()
        query = self._search.text().strip()
        items = self._repo.search(query)
        if not items:
            if query:
                empty = EmptyState("🔍", strings.KNOWLEDGE_NO_RESULTS_TITLE, strings.KNOWLEDGE_NO_RESULTS_BODY)
            else:
                empty = EmptyState("📚", strings.KNOWLEDGE_EMPTY_TITLE, strings.KNOWLEDGE_EMPTY_BODY)
            self._list.append(empty)
        for item in items:
            card = KnowledgeCard(item)
            card.clicked.connect(self._open)
            card.toggled.connect(self._toggle)
            self._list.append(card)

    def _toggle(self, item_id: int, enabled: bool) -> None:
        self._repo.set_enabled(item_id, enabled)
        self.changed.emit()
        # Let the switch animation finish before rebuilding the cards.
        QTimer.singleShot(150, self.reload)

    def _open(self, item_id: int | None) -> None:
        dialog = KnowledgeDialog(self._repo, self._repo.get(item_id) if item_id else None, self)
        if dialog.exec():
            self.reload()
            self.changed.emit()
