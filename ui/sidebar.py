"""Custom sidebar navigation rail (72 px wide, dark green).

Mirrors the WPF NavigationView layout: logo at top, icon buttons in the
middle, a close/quit button at the bottom.  Uses QPushButtons styled via
QSS with the Forest Floor palette.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import theme


# ── Icon helpers (text-drawn fallbacks when no image files) ──────────

def _text_icon(letter: str, size: int = 32, colour: str = "#ffffff") -> QIcon:
    """Create a simple icon with a single centred letter."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(colour))
    painter.setFont(QFont("Segoe UI", int(size * 0.45), QFont.Weight.DemiBold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)
    painter.end()
    return QIcon(pixmap)


# ── NavButton ────────────────────────────────────────────────────────

class NavButton(QPushButton):
    """A single sidebar navigation button with active-state styling."""

    def __init__(self, icon: QIcon, tooltip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setIcon(icon)
        self.setIconSize(QSize(24, 24))
        self.setToolTip(tooltip)
        self.setFixedSize(48, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self._apply_style(active=False)

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self._apply_style(active)

    def _apply_style(self, active: bool) -> None:
        bg = theme.SIDEBAR_ACTIVE if active else "transparent"
        hover = theme.SIDEBAR_HOVER
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
        """)


# ── Sidebar ──────────────────────────────────────────────────────────

class Sidebar(QFrame):
    """72 px vertical navigation rail.

    Signals
    -------
    page_requested(int)
        Emitted when a nav button is clicked.  The int is the page index
        (0 = Dashboard, 1 = Settings, …).
    quit_requested()
        Emitted when the bottom close/quit button is clicked.
    """

    page_requested = Signal(int)
    quit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(72)
        self.setStyleSheet(f"background-color: {theme.SIDEBAR_BG};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # ── logo placeholder ──
        self._logo = QPushButton(self)
        self._logo.setFixedSize(44, 44)
        self._logo.setIcon(_text_icon("B", 44, theme.ACCENT))
        self._logo.setIconSize(QSize(36, 36))
        self._logo.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self._logo.setToolTip("Biome")
        layout.addWidget(self._logo, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(20)

        # ── navigation buttons ──
        self._buttons: list[NavButton] = []
        nav_items = [
            (_text_icon("⌂", 32), "Dashboard"),
            (_text_icon("⚙", 32), "Settings"),
        ]
        for icon, tooltip in nav_items:
            btn = NavButton(icon, tooltip, self)
            self._buttons.append(btn)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # wire click → page index
        for idx, btn in enumerate(self._buttons):
            btn.clicked.connect(lambda checked, i=idx: self._on_nav_click(i))

        # ── spacer ──
        layout.addStretch()

        # ── quit button ──
        self._quit_btn = QPushButton(self)
        self._quit_btn.setIcon(_text_icon("✕", 32, theme.TEXT_SECONDARY))
        self._quit_btn.setIconSize(QSize(20, 20))
        self._quit_btn.setFixedSize(40, 40)
        self._quit_btn.setToolTip("Quit Biome")
        self._quit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._quit_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {theme.ERROR};
            }}
        """)
        self._quit_btn.clicked.connect(self.quit_requested.emit)
        layout.addWidget(self._quit_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # default selection
        self.select_page(0)

    # ── public ───────────────────────────────────────────────────────

    def select_page(self, index: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.set_active(i == index)

    # ── private ──────────────────────────────────────────────────────

    def _on_nav_click(self, index: int) -> None:
        self.select_page(index)
        self.page_requested.emit(index)
