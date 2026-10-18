"""Small reusable widgets and layout helpers."""

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractButton,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from telegram_ai_bot.ui.theme import C


def label(text: str = "", name: str = "", wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    if name:
        lbl.setObjectName(name)
    lbl.setWordWrap(wrap)
    return lbl


def vbox(parent: QWidget | None = None, margins=(0, 0, 0, 0), spacing: int = 8) -> QVBoxLayout:
    layout = QVBoxLayout(parent) if parent else QVBoxLayout()
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def hbox(parent: QWidget | None = None, margins=(0, 0, 0, 0), spacing: int = 8) -> QHBoxLayout:
    layout = QHBoxLayout(parent) if parent else QHBoxLayout()
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def button(text: str, name: str = "", tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    if name:
        btn.setObjectName(name)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def ltr_line_edit(text: str = "", placeholder: str = "") -> QLineEdit:
    """Line edit for URLs, keys and model names (left-to-right, monospace)."""
    edit = QLineEdit(text)
    edit.setPlaceholderText(placeholder)
    edit.setLayoutDirection(Qt.LeftToRight)
    edit.setProperty("ltr", True)
    return edit


def clear_layout(layout, keep: int = 0) -> None:
    """Remove and delete all items except the last `keep` (e.g. a trailing stretch)."""
    while layout.count() > keep:
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


class ScrollList(QScrollArea):
    """Vertical, scrollable list of widgets with a trailing stretch."""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        self.items = vbox(inner, (2, 2, 6, 2), 8)
        self.items.addStretch()
        self.setWidget(inner)

    def append(self, widget: QWidget) -> None:
        self.items.insertWidget(self.items.count() - 1, widget)

    def count(self) -> int:
        return self.items.count() - 1

    def clear(self) -> None:
        clear_layout(self.items, keep=1)

    def scroll_to_bottom(self) -> None:
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())


class EmptyState(QWidget):
    def __init__(self, icon: str, title: str, body: str):
        super().__init__()
        layout = vbox(self, (24, 40, 24, 40), 6)
        icon_label = label(icon)
        icon_label.setStyleSheet("font-size: 34px;")
        for widget in (icon_label, label(title, "EmptyTitle", True), label(body, "EmptyBody", True)):
            widget.setAlignment(Qt.AlignCenter)
            layout.addWidget(widget)


class Switch(QAbstractButton):
    """iOS-style toggle switch that respects right-to-left layouts."""

    WIDTH, HEIGHT, KNOB = 40, 22, 18

    def __init__(self, checked: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        super().setChecked(checked)
        self._offset = 1.0 if checked else 0.0
        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._animate)

    def sizeHint(self) -> QSize:
        return QSize(self.WIDTH, self.HEIGHT)

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    offset = Property(float, _get_offset, _set_offset)

    def _animate(self, checked: bool) -> None:
        self._animation.stop()
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        off, on = QColor("#D0D5DD"), QColor(C["primary"])
        t = self._offset
        track = QColor(
            int(off.red() + (on.red() - off.red()) * t),
            int(off.green() + (on.green() - off.green()) * t),
            int(off.blue() + (on.blue() - off.blue()) * t),
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(track)
        painter.drawRoundedRect(QRectF(0, 0, self.WIDTH, self.HEIGHT), self.HEIGHT / 2, self.HEIGHT / 2)
        travel = self.WIDTH - self.KNOB - 4
        x = 2 + travel * t
        if self.layoutDirection() == Qt.RightToLeft:
            x = self.WIDTH - self.KNOB - x  # "on" is on the left in RTL
        painter.setBrush(QColor("white"))
        painter.drawEllipse(QRectF(x, 2, self.KNOB, self.KNOB))
