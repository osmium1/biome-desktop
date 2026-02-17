"""Main application window — sidebar + stacked pages.

Composes the Sidebar, QStackedWidget (Dashboard / Settings), and an
optional frameless title bar.  Unlike the WPF version, Qt's QScrollArea
has no dead-zone scrolling problem, so we don't need manual
PreviewMouseWheel hacks.
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

from .sidebar import Sidebar
from .pages.dashboard import DashboardPage
from .pages.settings import SettingsPage


class MainWindow(QMainWindow):
    """Root window hosting sidebar navigation and page stack."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Biome")
        self.setMinimumSize(800, 560)
        self.resize(960, 640)

        # ── central widget ───────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)

        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── sidebar ──────────────────────────────────────────────────
        self._sidebar = Sidebar()
        self._sidebar.page_requested.connect(self._switch_page)
        self._sidebar.quit_requested.connect(self.close)
        outer.addWidget(self._sidebar)

        # ── page stack ───────────────────────────────────────────────
        self._stack = QStackedWidget()

        self.dashboard_page = DashboardPage()
        self.settings_page = SettingsPage()

        self._stack.addWidget(self.dashboard_page)   # index 0
        self._stack.addWidget(self.settings_page)     # index 1

        outer.addWidget(self._stack, stretch=1)

    # ── navigation ───────────────────────────────────────────────────

    @Slot(int)
    def _switch_page(self, index: int) -> None:
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)

    # ── window lifecycle ─────────────────────────────────────────────

    def closeEvent(self, event) -> None:  # noqa: N802
        """Hide to tray instead of quitting (if tray is active)."""
        # The app orchestrator can override this to minimise-to-tray
        event.accept()
