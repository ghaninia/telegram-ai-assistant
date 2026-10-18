"""Visual theme: fonts, color palette and the Qt stylesheet."""

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication, QStyleFactory

from telegram_ai_bot.paths import RESOURCES_DIR

FONT_FAMILY = "Vazirmatn FD"  # Vazirmatn with Persian digits (OFL licensed, bundled)

# Palette inspired by Telegram.
C = {
    "bg": "#F2F4F7",
    "card": "#FFFFFF",
    "border": "#E4E7EC",
    "text": "#1D2433",
    "muted": "#6B7280",
    "faint": "#9AA1AE",
    "primary": "#2AABEE",
    "primary_dark": "#1E96D4",
    "primary_soft": "#E8F5FD",
    "success": "#1F9D62",
    "success_soft": "#E7F6EE",
    "warn": "#B7791F",
    "warn_soft": "#FEF5E1",
    "danger": "#E5484D",
    "danger_soft": "#FDECEC",
    "bubble_in": "#F1F3F6",
    "bubble_out": "#E3F3FC",
}


STYLESHEET = f"""
* {{
    font-family: "{FONT_FAMILY}";
    color: {C['text']};
}}
QMainWindow, QDialog {{ background: {C['bg']}; }}
QToolTip {{
    background: {C['text']}; color: white; border: none; padding: 6px 8px; border-radius: 6px;
}}

/* ---------- side panel ---------- */
#SidePanel {{ background: {C['card']}; border-right: 1px solid {C['border']}; }}
#AppTitle {{ font-size: 17px; font-weight: 700; }}
#AppSubtitle {{ font-size: 12px; color: {C['muted']}; }}
#SectionTitle {{ font-size: 12px; font-weight: 600; color: {C['muted']}; }}

#StatusCard {{
    background: {C['bg']}; border: 1px solid {C['border']}; border-radius: 14px;
}}
#StatusText {{ font-size: 15px; font-weight: 700; }}
#StatusSub {{ font-size: 12px; color: {C['muted']}; }}
#StatValue {{ font-size: 18px; font-weight: 700; }}
#StatLabel {{ font-size: 11px; color: {C['muted']}; }}

/* ---------- buttons ---------- */
QPushButton {{
    background: {C['card']}; border: 1px solid {C['border']}; border-radius: 10px;
    padding: 8px 14px; font-size: 13px; font-weight: 500;
}}
QPushButton:hover {{ background: {C['bg']}; }}
QPushButton:pressed {{ background: {C['border']}; }}
QPushButton:disabled {{ color: {C['faint']}; background: {C['card']}; }}

QPushButton#Primary {{
    background: {C['primary']}; color: white; border: none; font-size: 14px; font-weight: 700;
    padding: 12px; border-radius: 12px;
}}
QPushButton#Primary:hover {{ background: {C['primary_dark']}; }}
QPushButton#Primary:disabled {{ background: {C['faint']}; }}
QPushButton#Danger {{
    background: {C['danger_soft']}; color: {C['danger']}; border: 1px solid #F7C8CA;
    font-size: 14px; font-weight: 700; padding: 12px; border-radius: 12px;
}}
QPushButton#Danger:hover {{ background: #FBDADB; }}
QPushButton#Ghost {{ border: none; background: transparent; color: {C['muted']}; padding: 6px 8px; }}
QPushButton#Ghost:hover {{ background: {C['bg']}; color: {C['text']}; }}
QPushButton#IconButton {{
    border: 1px solid {C['border']}; border-radius: 10px; padding: 0; font-size: 16px;
    min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px;
}}
QPushButton#DangerText {{ border: none; background: transparent; color: {C['danger']}; }}
QPushButton#DangerText:hover {{ background: {C['danger_soft']}; }}

/* ---------- segmented tabs ---------- */
#Segment {{ background: {C['bg']}; border-radius: 10px; }}
#Segment QPushButton {{
    border: none; background: transparent; border-radius: 8px; padding: 7px; color: {C['muted']};
    font-weight: 600;
}}
#Segment QPushButton:checked {{ background: {C['card']}; color: {C['text']}; border: 1px solid {C['border']}; }}

/* ---------- inputs ---------- */
QLineEdit, QPlainTextEdit {{
    background: {C['card']}; border: 1px solid {C['border']}; border-radius: 10px;
    padding: 8px 10px; font-size: 13px; selection-background-color: {C['primary']};
}}
QLineEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {C['primary']}; }}
QLineEdit[ltr="true"] {{ font-family: "Menlo", "{FONT_FAMILY}"; font-size: 12px; }}
QLabel#FieldLabel {{ font-size: 12px; font-weight: 600; }}
QLabel#Hint {{ font-size: 11px; color: {C['muted']}; }}

QCheckBox {{ spacing: 8px; font-size: 13px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border: 1px solid {C['faint']}; border-radius: 5px; background: white;
}}
QCheckBox::indicator:checked {{ background: {C['primary']}; border-color: {C['primary']}; }}

/* ---------- cards and lists ---------- */
#Card {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 12px; }}
#KnowledgeCard {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 12px; }}
#KnowledgeCard:hover {{ border-color: {C['primary']}; }}
#CardTitle {{ font-size: 13px; font-weight: 700; }}
#CardBody {{ font-size: 12px; color: {C['muted']}; }}
#EmptyTitle {{ font-size: 14px; font-weight: 700; color: {C['muted']}; }}
#EmptyBody {{ font-size: 12px; color: {C['faint']}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #CBD1DA; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------- activity events ---------- */
#EvTime {{ font-size: 10px; color: {C['faint']}; }}
#EvInfo {{ font-size: 12px; color: {C['muted']}; }}
#EvBubbleIn {{ background: {C['bubble_in']}; border-radius: 14px; }}
#EvBubbleOut {{ background: {C['bubble_out']}; border-radius: 14px; }}
#EvBubbleLabel {{ font-size: 10px; font-weight: 700; color: {C['muted']}; }}
#EvBubbleText {{ font-size: 13px; }}
#EvSuccess {{ background: {C['success_soft']}; border-radius: 10px; }}
#EvWarn {{ background: {C['warn_soft']}; border-radius: 10px; }}
#EvError {{ background: {C['danger_soft']}; border-radius: 10px; }}
#EvTitleSuccess {{ font-size: 12px; font-weight: 700; color: {C['success']}; }}
#EvTitleWarn {{ font-size: 12px; font-weight: 700; color: {C['warn']}; }}
#EvTitleError {{ font-size: 12px; font-weight: 700; color: {C['danger']}; }}
#EvHint {{ font-size: 12px; color: {C['text']}; }}
#EvTyping {{ font-size: 12px; color: {C['primary_dark']}; font-weight: 600; }}

/* ---------- settings ---------- */
#SettingsSection {{ background: {C['card']}; border: 1px solid {C['border']}; border-radius: 14px; }}
#SectionHeader {{ font-size: 14px; font-weight: 700; }}
"""


def load_fonts() -> None:
    for path in sorted((RESOURCES_DIR / "fonts").glob("*.ttf")):
        QFontDatabase.addApplicationFont(str(path))


def apply_theme(app: QApplication) -> None:
    load_fonts()
    # Consistent light look regardless of the system dark mode.
    app.setStyle(QStyleFactory.create("Fusion"))
    palette = QPalette()
    for role, color in (
        (QPalette.Window, C["bg"]),
        (QPalette.Base, C["card"]),
        (QPalette.AlternateBase, C["bg"]),
        (QPalette.Text, C["text"]),
        (QPalette.WindowText, C["text"]),
        (QPalette.ButtonText, C["text"]),
        (QPalette.Button, C["card"]),
        (QPalette.Highlight, C["primary"]),
        (QPalette.HighlightedText, "#FFFFFF"),
        (QPalette.PlaceholderText, C["faint"]),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    font = QFont(FONT_FAMILY, 13)
    font.setHintingPreference(QFont.PreferNoHinting)
    app.setFont(font)
    app.setStyleSheet(STYLESHEET)
