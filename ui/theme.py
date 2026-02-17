"""Material Design dark theme for the Biome desktop client.

Wraps *qt-material* with a custom colour palette and exports semantic
token constants that the rest of the UI can import.  Call
``apply_theme(app)`` once before any widget is created.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtWidgets import QApplication

# ── asset directories ──────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = str(_ROOT / "icons")
FONTS_DIR = str(_ROOT / "fonts")


def icon_path(name: str) -> str:
    """Return the full path to an SVG icon by stem name."""
    return os.path.join(ICONS_DIR, f"{name}.svg")


# ── colour tokens  (Material teal-dark palette) ─────────────────────
PRIMARY        = "#009688"    # teal 500
PRIMARY_LIGHT  = "#4db6ac"    # teal 300
PRIMARY_DARK   = "#00796b"    # teal 700
ACCENT         = "#4caf50"    # green 500 — kept for Biome brand
ACCENT_LIGHT   = "#81c784"    # green 300

BACKGROUND     = "#121218"    # deepest layer
BACKGROUND_ALT = "#1a1a24"    # page content area
SURFACE        = "#22222e"    # cards / panels
SURFACE_LIGHT  = "#2c2c3a"    # hover / elevated cards
SURFACE_HIGH   = "#363646"    # highest elevation (footer bar, popovers)
SIDEBAR_BG     = "#16161e"    # nav rail — darkest
SIDEBAR_HOVER  = "#262634"
SIDEBAR_ACTIVE = "#009688"    # primary teal

TEXT_PRIMARY   = "#e0e0e0"
TEXT_SECONDARY = "#8e8e9e"
TEXT_DISABLED  = "#555566"
BORDER         = "#2e2e3e"
BORDER_LIGHT   = "#3a3a4c"
INPUT_BG       = "#1a1a26"
ERROR          = "#ef5350"
SENT_BADGE     = "#81c784"

# ── font stack ───────────────────────────────────────────────────────
FONT_FAMILY = '"Inter", "Rubik", "Segoe UI Variable", system-ui, sans-serif'


# ── override QSS (applied on top of qt-material) ────────────────────
_OVERRIDE_QSS = f"""
/* ─── Global base ─── */
QMainWindow, QWidget {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}

/* ─── Sidebar rail ─── */
#sidebar {{
    background-color: {SIDEBAR_BG};
    border: none;
}}

/* ─── Card (QGroupBox styling) ─── */
QGroupBox {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 24px;
    padding: 20px 18px 14px 18px;
    font-weight: 600;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    left: 10px;
    top: 2px;
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

/* ─── Scroll bars ─── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    min-height: 30px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {PRIMARY};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ─── Flat scroll area ─── */
QScrollArea {{
    border: none;
    background: transparent;
}}

/* ─── Activity log ─── */
QListWidget {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 4px;
    font-size: 12px;
}}
QListWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
}}
QListWidget::item:selected {{
    background-color: {SURFACE_LIGHT};
}}

/* ─── Page content area — slightly lighter than window bg ─── */
QStackedWidget > QWidget {{
    background-color: {BACKGROUND_ALT};
}}

/* ─── Heading labels ─── */
QLabel[class="heading"] {{
    font-size: 20px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    background: transparent;
}}
QLabel[class="subheading"] {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
    background: transparent;
}}
QLabel[class="card-title"] {{
    font-size: 13px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    background: transparent;
}}
QLabel[class="card-value"] {{
    font-size: 13px;
    color: {TEXT_SECONDARY};
    background: transparent;
}}

/* ─── Primary button ─── */
QPushButton[class="primary"] {{
    background-color: {PRIMARY};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 13px;
    min-width: 60px;
}}
QPushButton[class="primary"]:hover {{
    background-color: {PRIMARY_LIGHT};
}}
QPushButton[class="primary"]:pressed {{
    background-color: {PRIMARY_DARK};
}}

/* ─── Secondary / outline button ─── */
QPushButton[class="secondary"] {{
    background-color: {SURFACE_LIGHT};
    border: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    min-width: 80px;
}}
QPushButton[class="secondary"]:hover {{
    border-color: {PRIMARY};
    color: {PRIMARY_LIGHT};
    background-color: {SURFACE_HIGH};
}}
QPushButton[class="secondary"]:pressed {{
    background-color: {SURFACE};
}}

/* ─── Footer bar ─── */
#footer_bar {{
    background-color: {SURFACE};
    border-top: 1px solid {BORDER};
    padding: 8px 0;
}}

/* ─── Nav buttons in sidebar ─── */
QToolButton#nav_btn {{
    background: transparent;
    border: none;
    border-radius: 10px;
    padding: 8px;
}}
QToolButton#nav_btn:hover {{
    background: {SIDEBAR_HOVER};
}}
QToolButton#nav_btn:pressed {{
    background: {PRIMARY_DARK};
}}
QToolButton#nav_btn:checked {{
    background: rgba(0, 150, 136, 0.25);
    border: 1px solid rgba(0, 150, 136, 0.4);
}}

/* ─── Title bar ─── */
#titlebar {{
    background-color: {SIDEBAR_BG};
    border-bottom: 1px solid {BORDER};
}}
#titlebar QPushButton {{
    background: transparent;
    border: none;
    padding: 6px 14px;
    color: {TEXT_SECONDARY};
    font-size: 14px;
}}
#titlebar QPushButton:hover {{
    background: {SURFACE_LIGHT};
}}
#titlebar #btn_close:hover {{
    background: {ERROR};
    color: #ffffff;
}}

/* ─── QLineEdit ─── */
QLineEdit {{
    background-color: {INPUT_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {PRIMARY};
    min-height: 20px;
}}
QLineEdit:focus {{
    border-color: {PRIMARY};
}}

/* ─── QCheckBox ─── */
QCheckBox {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {BORDER};
    background: {INPUT_BG};
}}
QCheckBox::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}

/* ─── QComboBox ─── */
QComboBox {{
    background-color: {INPUT_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}
QComboBox:hover {{
    border-color: {PRIMARY};
}}
QComboBox QAbstractItemView {{
    background-color: {SURFACE};
    color: {TEXT_PRIMARY};
    selection-background-color: {PRIMARY_DARK};
}}

/* ─── Tooltips ─── */
QToolTip {{
    background-color: {SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}}

/* ─── Tray menu ─── */
QMenu {{
    background-color: {SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 2px 0;
    font-size: 12px;
}}
QMenu::item {{
    padding: 4px 24px 4px 12px;
    min-height: 16px;
}}
QMenu::item:selected {{
    background-color: {PRIMARY_DARK};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 2px 8px;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply Material dark-teal theme + Biome overrides."""
    from PySide6.QtGui import QFontDatabase
    from qt_material import apply_stylesheet

    # ── register bundled Inter font ───────────────────────────────
    fonts_path = Path(FONTS_DIR)
    if fonts_path.exists():
        for ttf in fonts_path.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(ttf))

    extra = {
        "density_scale": "0",
        "font_family": "Inter, Rubik, Segoe UI Variable, sans-serif",
        "font_size": "13px",
    }

    apply_stylesheet(
        app,
        theme="dark_teal.xml",
        extra=extra,
        css_file=None,
    )

    # layer our overrides on top
    current = app.styleSheet() or ""
    app.setStyleSheet(current + "\n" + _OVERRIDE_QSS)
