"""Main application window — frameless, with custom title bar.

Composes the TitleBar, Sidebar, and a QStackedWidget holding the
Dashboard and Settings pages.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .titlebar import TitleBar
from .sidebar import Sidebar
from .pages.dashboard import DashboardPage
from .pages.settings import SettingsPage


class MainWindow(QMainWindow):
    """Root window hosting title bar, sidebar navigation, and page stack."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Biome")
        self.setMinimumSize(800, 560)
        self.resize(960, 640)

        # frameless window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # ── central widget ───────────────────────────────────────────
        central = QWidget()
        central.setStyleSheet(f"background-color: {theme.BACKGROUND};")
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── custom title bar ─────────────────────────────────────────
        self._titlebar = TitleBar()
        outer.addWidget(self._titlebar)

        # ── body: sidebar + pages ────────────────────────────────────
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_requested.connect(self._switch_page)
        self._sidebar.quit_requested.connect(self.close)
        body_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()

        self.dashboard_page = DashboardPage()
        self.settings_page = SettingsPage()

        self._stack.addWidget(self.dashboard_page)   # index 0
        self._stack.addWidget(self.settings_page)     # index 1

        body_layout.addWidget(self._stack, stretch=1)
        outer.addWidget(body, stretch=1)

    # ── navigation ───────────────────────────────────────────────────

    @Slot(int)
    def _switch_page(self, index: int) -> None:
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)

    # ── window lifecycle ─────────────────────────────────────────────

    def closeEvent(self, event) -> None:  # noqa: N802
        """Hide to tray instead of quitting (if tray is active)."""
        event.accept()
