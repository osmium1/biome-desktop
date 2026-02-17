"""Navigation sidebar rail with SVG icon buttons.

A slim 64 px column housing a logo, page-navigation tool-buttons, and a
quit button.  All styling is done via QSS pseudo-states defined in
``theme._OVERRIDE_QSS`` — no inline ``setStyleSheet`` calls.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import theme


# ── NavButton ────────────────────────────────────────────────────────

class NavButton(QToolButton):
    """Checkable navigation button styled entirely through QSS."""

    def __init__(
        self,
        icon_name: str,
        tooltip: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("nav_btn")
        self.setIcon(QIcon(theme.icon_path(icon_name)))
        self.setIconSize(QSize(22, 22))
        self.setToolTip(tooltip)
        self.setFixedSize(44, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)


# ── Sidebar ──────────────────────────────────────────────────────────

class Sidebar(QFrame):
    """64 px vertical navigation rail.

    Signals
    -------
    page_requested(int)
        Page index the user wants to switch to.
    quit_requested()
        User clicked the quit / close button.
    """

    page_requested = Signal(int)
    quit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(64)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # ── logo ─────────────────────────────────────────────────────
        self._logo = QToolButton(self)
        self._logo.setObjectName("nav_btn")
        self._logo.setIcon(QIcon(theme.icon_path("send")))
        self._logo.setIconSize(QSize(28, 28))
        self._logo.setFixedSize(44, 44)
        self._logo.setToolTip("Biome")
        self._logo.setCheckable(False)
        layout.addWidget(self._logo, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addSpacing(16)

        # ── navigation buttons ───────────────────────────────────────
        self._buttons: list[NavButton] = []
        nav_items = [
            ("dashboard", "Dashboard"),
            ("settings",  "Settings"),
        ]
        for icon_name, tooltip in nav_items:
            btn = NavButton(icon_name, tooltip, self)
            self._buttons.append(btn)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        for idx, btn in enumerate(self._buttons):
            btn.clicked.connect(lambda checked, i=idx: self._on_nav_click(i))

        # ── spacer ───────────────────────────────────────────────────
        layout.addStretch()

        # ── quit button ──────────────────────────────────────────────
        self._quit_btn = QToolButton(self)
        self._quit_btn.setObjectName("nav_btn")
        self._quit_btn.setIcon(QIcon(theme.icon_path("close")))
        self._quit_btn.setIconSize(QSize(18, 18))
        self._quit_btn.setFixedSize(36, 36)
        self._quit_btn.setToolTip("Quit Biome")
        self._quit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._quit_btn.clicked.connect(self.quit_requested.emit)
        layout.addWidget(self._quit_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # default selection
        self.select_page(0)

    # ── public ───────────────────────────────────────────────────────

    def select_page(self, index: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)

    # ── private ──────────────────────────────────────────────────────

    def _on_nav_click(self, index: int) -> None:
        self.select_page(index)
        self.page_requested.emit(index)
