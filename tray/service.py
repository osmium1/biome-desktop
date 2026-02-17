"""System tray icon with context menu and state indicators.

Uses QSystemTrayIcon which is natively supported on Windows.  The tray
owns five visual states (idle, waiting, sending, sent, error) that map
directly to the C# TrayService states.
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QAction, QColor, QIcon, QPixmap, QPainter, QFont
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QApplication

logger = logging.getLogger(__name__)


class TrayState(Enum):
    IDLE = auto()
    WAITING = auto()
    SENDING = auto()
    SENT = auto()
    ERROR = auto()


# colour for each state (used to draw fallback icons)
_STATE_COLOURS: dict[TrayState, str] = {
    TrayState.IDLE: "#4caf50",
    TrayState.WAITING: "#ff9800",
    TrayState.SENDING: "#fdd835",
    TrayState.SENT: "#81c784",
    TrayState.ERROR: "#ef5350",
}


def _make_icon(colour: str, size: int = 64) -> QIcon:
    """Generate a simple coloured circle icon as a fallback."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(colour))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)
    # draw "B" in the centre
    painter.setPen(QColor("#ffffff"))
    painter.setFont(QFont("Segoe UI", int(size * 0.35), QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "B")
    painter.end()
    return QIcon(pixmap)


from PySide6.QtCore import Qt


class TrayService(QObject):
    """Manages the system tray icon, menu, and state transitions.

    Signals
    -------
    state_changed(TrayState)
        Emitted whenever the tray state changes (used by the app to
        trigger the SpeedBoost overlay, for example).
    send_requested()
        Emitted when the user clicks "Send Clipboard" from the menu.
    show_requested()
        Emitted when the user activates (double-clicks) the tray icon.
    quit_requested()
        Emitted when the user clicks "Quit" from the tray menu.
    """

    state_changed = Signal(object)  # TrayState
    send_requested = Signal()
    show_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._state = TrayState.IDLE
        self._icons: dict[TrayState, QIcon] = {
            state: _make_icon(colour) for state, colour in _STATE_COLOURS.items()
        }

        self._tray = QSystemTrayIcon(self._icons[TrayState.IDLE], parent)
        self._tray.setToolTip("Biome — idle")
        self._tray.activated.connect(self._on_activated)

        # ── context menu ─────────────────────────────────────────────
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #232823;
                color: #e0e0e0;
                border: 1px solid #2e352e;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #266332;
            }
        """)

        self._send_action = QAction("Send Clipboard", menu)
        self._send_action.triggered.connect(self.send_requested.emit)
        menu.addAction(self._send_action)

        menu.addSeparator()

        show_action = QAction("Show Window", menu)
        show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(show_action)

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

    # ── public API ───────────────────────────────────────────────────

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    @property
    def state(self) -> TrayState:
        return self._state

    def set_state(self, new_state: TrayState) -> None:
        if new_state == self._state:
            return
        self._state = new_state
        icon = self._icons.get(new_state, self._icons[TrayState.IDLE])
        self._tray.setIcon(icon)
        self._tray.setToolTip(f"Biome — {new_state.name.lower()}")
        self.state_changed.emit(new_state)

    def notify(self, title: str, message: str) -> None:
        if self._tray.supportsMessages():
            self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    # ── private ──────────────────────────────────────────────────────

    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()
