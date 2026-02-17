"""Custom frameless title bar with minimize / maximize / close controls.

Styled entirely via QSS selectors in ``theme._OVERRIDE_QSS`` —
no inline ``setStyleSheet`` calls.  Supports window dragging and
double-click to toggle maximize.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from . import theme


class TitleBar(QWidget):
    """Draggable title bar with window controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("titlebar")
        self.setFixedHeight(36)

        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(0)

        # ── app title ────────────────────────────────────────────────
        self._title = QLabel("Biome")
        self._title.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;"
            f" font-family: {theme.FONT_FAMILY}; background: transparent;"
        )
        layout.addWidget(self._title)

        layout.addStretch()

        # ── window controls ──────────────────────────────────────────
        btn_size = 36

        self._btn_minimize = QPushButton()
        self._btn_minimize.setIcon(QIcon(theme.icon_path("minimize")))
        self._btn_minimize.setFixedSize(btn_size + 10, btn_size)
        self._btn_minimize.setToolTip("Minimize")
        self._btn_minimize.clicked.connect(self._on_minimize)
        layout.addWidget(self._btn_minimize)

        self._btn_maximize = QPushButton()
        self._btn_maximize.setIcon(QIcon(theme.icon_path("maximize")))
        self._btn_maximize.setFixedSize(btn_size + 10, btn_size)
        self._btn_maximize.setToolTip("Maximize")
        self._btn_maximize.clicked.connect(self._on_maximize)
        layout.addWidget(self._btn_maximize)

        self._btn_close = QPushButton()
        self._btn_close.setObjectName("btn_close")
        self._btn_close.setIcon(QIcon(theme.icon_path("close")))
        self._btn_close.setFixedSize(btn_size + 10, btn_size)
        self._btn_close.setToolTip("Close")
        self._btn_close.clicked.connect(self._on_close)
        layout.addWidget(self._btn_close)

    # ── window helpers (resolved at runtime) ─────────────────────────

    def _main_window(self):
        return self.window()

    # ── button callbacks ─────────────────────────────────────────────

    def _on_minimize(self) -> None:
        self._main_window().showMinimized()

    def _on_maximize(self) -> None:
        win = self._main_window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()

    def _on_close(self) -> None:
        self._main_window().close()

    # ── drag support ─────────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._main_window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._main_window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_maximize()
