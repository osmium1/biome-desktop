"""Forest Floor dark theme for the Biome desktop client.

Defines colours, QSS stylesheets, and QPalette overrides that give the
app its signature dark-green aesthetic.  Every widget picks up these
styles automatically once ``apply_theme`` is called on the QApplication.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


# ── colour tokens ────────────────────────────────────────────────────
BACKGROUND       = "#1a1e1a"   # main surface
SURFACE          = "#232823"   # cards / panels
SIDEBAR_BG       = "#15291a"   # dark-green rail
SIDEBAR_HOVER    = "#1e3d26"   # hovered nav item
SIDEBAR_ACTIVE   = "#266332"   # selected nav item
ACCENT           = "#4caf50"   # primary green
ACCENT_HOVER     = "#66bb6a"
TEXT_PRIMARY     = "#e0e0e0"
TEXT_SECONDARY   = "#9e9e9e"
TEXT_DISABLED    = "#616161"
BORDER           = "#2e352e"
INPUT_BG         = "#1e241e"
ERROR            = "#ef5350"
SENT_BADGE       = "#81c784"   # success indicator


# ── global QSS ──────────────────────────────────────────────────────
STYLESHEET = f"""
/* ---- Base ---- */
QMainWindow, QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}}

/* ---- Scroll area ---- */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: {SURFACE};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    min-height: 30px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ---- Cards ---- */
QFrame[frameShape="1"] {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}

/* ---- Labels ---- */
QLabel {{
    background: transparent;
    color: {TEXT_PRIMARY};
}}
QLabel[class="heading"] {{
    font-size: 18px;
    font-weight: 600;
}}
QLabel[class="subheading"] {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
}}

/* ---- Buttons ---- */
QPushButton {{
    background-color: {ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton:pressed {{
    background-color: #388e3c;
}}
QPushButton:disabled {{
    background-color: {TEXT_DISABLED};
    color: {TEXT_SECONDARY};
}}
QPushButton[class="secondary"] {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
}}
QPushButton[class="secondary"]:hover {{
    border-color: {ACCENT};
}}

/* ---- Line edits ---- */
QLineEdit {{
    background-color: {INPUT_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}

/* ---- Toggle / Checkbox ---- */
QCheckBox {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {BORDER};
    background: {INPUT_BG};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

/* ---- Combo box ---- */
QComboBox {{
    background-color: {INPUT_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
}}
QComboBox:hover {{
    border-color: {ACCENT};
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    color: {TEXT_PRIMARY};
    selection-background-color: {SIDEBAR_ACTIVE};
}}

/* ---- Separator lines ---- */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {BORDER};
}}

/* ---- Tooltips ---- */
QToolTip {{
    background-color: {SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 4px 8px;
    border-radius: 4px;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply the Forest Floor dark theme to the entire application."""

    app.setStyleSheet(STYLESHEET)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BACKGROUND))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(INPUT_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(TEXT_DISABLED))

    app.setPalette(palette)
