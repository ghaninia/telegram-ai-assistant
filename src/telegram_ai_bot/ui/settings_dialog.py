"""Settings dialog: Gemini connection, proxy, persona and advanced model options."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QWidget,
)

from telegram_ai_bot.ai.agent import ReplyAgent
from telegram_ai_bot.ai.errors import AIError
from telegram_ai_bot.core.models import ChatMessage, Direction
from telegram_ai_bot.core.prompts import DEFAULT_SYSTEM_PROMPT
from telegram_ai_bot.storage.settings import AppSettings, SettingsRepository, parse_model_list
from telegram_ai_bot.ui import strings
from telegram_ai_bot.ui.theme import C
from telegram_ai_bot.ui.widgets import button, hbox, label, ltr_line_edit, vbox


class SettingsDialog(QDialog):
    _test_finished = Signal(bool, str)  # ok, message

    def __init__(self, repo: SettingsRepository, parent: QWidget | None = None):
        super().__init__(parent)
        self._repo = repo
        self._original = repo.load()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._test_finished.connect(self._show_test_result)
        self.setWindowTitle(strings.SETTINGS_TITLE)
        self.setMinimumSize(620, 700)
        s = self._original

        # --- connection ---
        self._api_key = ltr_line_edit(s.api_key, strings.API_KEY_PLACEHOLDER)
        self._api_key.setEchoMode(QLineEdit.Password)
        show = QCheckBox(strings.SHOW)
        show.toggled.connect(lambda on: self._api_key.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        key_row = hbox()
        key_row.addWidget(self._api_key, 1)
        key_row.addWidget(show)

        self._test_button = button(strings.TEST_CONNECTION)
        self._test_button.clicked.connect(self._test_connection)
        self._test_result = label("", "Hint", True)
        test_row = hbox()
        test_row.addWidget(self._test_button)
        test_row.addWidget(self._test_result, 1)

        # --- proxy ---
        self._proxy = ltr_line_edit(s.proxy, "socks5://127.0.0.1:1080")

        # --- persona ---
        self._prompt = QPlainTextEdit(s.system_prompt)
        self._prompt.setMinimumHeight(180)
        reset = button(strings.RESET_PROMPT, "Ghost")
        reset.clicked.connect(lambda: self._prompt.setPlainText(DEFAULT_SYSTEM_PROMPT))
        reset_row = hbox()
        reset_row.addStretch()
        reset_row.addWidget(reset)

        # --- advanced ---
        self._model = ltr_line_edit(s.model)
        self._fallbacks = ltr_line_edit(",".join(s.fallback_models))
        self._base_url = ltr_line_edit(s.base_url)
        self._advanced = self._section(strings.SECTION_ADVANCED, [
            label(strings.FIELD_MODEL, "FieldLabel"), self._model,
            label(strings.FIELD_FALLBACKS, "FieldLabel", True), self._fallbacks,
            label(strings.FIELD_BASE_URL, "FieldLabel"), self._base_url,
        ])
        self._advanced.hide()
        toggle_advanced = button(strings.SHOW_ADVANCED, "Ghost")
        toggle_advanced.clicked.connect(lambda: self._toggle_advanced(toggle_advanced))
        advanced_row = hbox()
        advanced_row.addWidget(toggle_advanced)
        advanced_row.addStretch()

        content = QWidget()
        content_layout = vbox(content, (20, 20, 20, 10), 14)
        content_layout.addWidget(self._section(strings.SECTION_CONNECTION, [
            label(strings.FIELD_API_KEY, "FieldLabel"), key_row,
            label(strings.API_KEY_HINT, "Hint", True), test_row,
        ]))
        content_layout.addWidget(self._section(strings.SECTION_PROXY, [
            self._proxy, label(strings.PROXY_HINT, "Hint", True),
        ]))
        content_layout.addWidget(self._section(strings.SECTION_PERSONA, [
            label(strings.PERSONA_HINT, "Hint", True), self._prompt, reset_row,
        ]))
        content_layout.addLayout(advanced_row)
        content_layout.addWidget(self._advanced)
        content_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        save = button(strings.SAVE, "Primary")
        save.setMinimumWidth(130)
        save.clicked.connect(self._save)
        cancel = button(strings.CANCEL)
        cancel.clicked.connect(self.reject)
        footer = hbox(margins=(20, 10, 20, 16))
        footer.addStretch()
        footer.addWidget(cancel)
        footer.addWidget(save)

        layout = vbox(self, spacing=0)
        layout.addWidget(scroll, 1)
        layout.addLayout(footer)

    @staticmethod
    def _section(title: str, items: list) -> QFrame:
        frame = QFrame()
        frame.setObjectName("SettingsSection")
        layout = vbox(frame, (18, 16, 18, 16), 8)
        layout.addWidget(label(title, "SectionHeader"))
        for item in items:
            if isinstance(item, QHBoxLayout):
                layout.addLayout(item)
            else:
                layout.addWidget(item)
        return frame

    def _toggle_advanced(self, toggle) -> None:
        self._advanced.setVisible(not self._advanced.isVisible())
        toggle.setText(strings.HIDE_ADVANCED if self._advanced.isVisible() else strings.SHOW_ADVANCED)

    def _current(self) -> AppSettings:
        return replace(
            self._original,
            api_key=self._api_key.text().strip(),
            proxy=self._proxy.text().strip(),
            system_prompt=self._prompt.toPlainText().strip() or DEFAULT_SYSTEM_PROMPT,
            model=self._model.text().strip() or AppSettings().model,
            fallback_models=parse_model_list(self._fallbacks.text()),
            base_url=self._base_url.text().strip() or AppSettings().base_url,
        )

    def _test_connection(self) -> None:
        """Send a tiny request with the (possibly unsaved) values on screen."""
        self._test_button.setEnabled(False)
        self._test_result.setStyleSheet(f"color: {C['muted']};")
        self._test_result.setText(strings.TESTING)
        settings = replace(self._current(), fallback_models=())
        probe = [ChatMessage("probe", Direction.INCOMING, strings.TEST_PROMPT)]

        def work() -> None:
            try:
                ReplyAgent(settings, knowledge=[]).reply(probe)
                ok, message = True, strings.TEST_OK
            except AIError as e:
                title, hint = strings.ai_error_message(e)
                ok, message = False, f"⛔ {title}\n{hint}"
            with suppress(RuntimeError):  # the dialog may have been closed meanwhile
                self._test_finished.emit(ok, message)

        self._executor.submit(work)

    def _show_test_result(self, ok: bool, message: str) -> None:
        self._test_button.setEnabled(True)
        color = C["success"] if ok else C["danger"]
        self._test_result.setStyleSheet(f"color: {color}; font-weight: 600;")
        self._test_result.setText(message)

    def _save(self) -> None:
        settings = self._current()
        self._repo.save(settings)
        if settings.proxy != self._original.proxy:
            QMessageBox.information(self, strings.PROXY_CHANGED_TITLE, strings.PROXY_CHANGED_BODY)
        self.accept()

    def done(self, result: int) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        super().done(result)
