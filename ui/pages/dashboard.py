"""Dashboard page — primary clipboard-send console.

Layout (top → bottom):
  • Page heading + subheading
  • "Send Clipboard" card with a button that grabs the system clipboard
    and dispatches it to the backend API
  • Status cards row (connection status, last sent item)
  • Activity log (scrollable list of recent events)
"""

from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import theme

logger = logging.getLogger(__name__)


# ── helper: card container ───────────────────────────────────────────

def _card(parent: QWidget | None = None) -> QFrame:
    """Return a styled card frame."""
    frame = QFrame(parent)
    frame.setFrameShape(QFrame.Shape.Box)
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: {theme.SURFACE};
            border: 1px solid {theme.BORDER};
            border-radius: 8px;
        }}
    """)
    return frame


# ── DashboardPage ────────────────────────────────────────────────────

class DashboardPage(QWidget):
    """Console / home page shown after app launch."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # service references — wired later by app.py
        self._api_client = None
        self._clipboard_watcher = None

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(0)

        # ── header ───────────────────────────────────────────────────
        heading = QLabel("Console")
        heading.setProperty("class", "heading")
        root.addWidget(heading)

        sub = QLabel("Send clipboard contents to your linked devices.")
        sub.setProperty("class", "subheading")
        root.addWidget(sub)
        root.addSpacing(20)

        # ── scrollable body ──────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(16)

        # ── send card ────────────────────────────────────────────────
        send_card = _card(body)
        sc_lay = QVBoxLayout(send_card)
        sc_lay.setContentsMargins(20, 16, 20, 16)
        sc_lay.setSpacing(8)
        sc_lay.addWidget(QLabel("Clipboard Dispatch"))
        self._send_btn = QPushButton("Send Clipboard")
        self._send_btn.setFixedHeight(40)
        self._send_btn.clicked.connect(self._on_send_clicked)
        sc_lay.addWidget(self._send_btn)
        body_lay.addWidget(send_card)

        # ── status cards row ─────────────────────────────────────────
        row = QHBoxLayout()
        row.setSpacing(12)

        # connection status card
        conn_card = _card(body)
        cc_lay = QVBoxLayout(conn_card)
        cc_lay.setContentsMargins(16, 12, 16, 12)
        cc_lay.addWidget(QLabel("Connection"))
        self._conn_label = QLabel("Checking…")
        self._conn_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        cc_lay.addWidget(self._conn_label)
        conn_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(conn_card)

        # last sent card
        last_card = _card(body)
        lc_lay = QVBoxLayout(last_card)
        lc_lay.setContentsMargins(16, 12, 16, 12)
        lc_lay.addWidget(QLabel("Last Sent"))
        self._last_label = QLabel("Nothing yet")
        self._last_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY};")
        lc_lay.addWidget(self._last_label)
        last_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(last_card)

        body_lay.addLayout(row)

        # ── activity log ─────────────────────────────────────────────
        log_label = QLabel("Activity")
        log_label.setStyleSheet("font-weight: 600; margin-top: 8px;")
        body_lay.addWidget(log_label)

        self._activity_list = QListWidget()
        self._activity_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.SURFACE};
                border: 1px solid {theme.BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {theme.BORDER};
                color: {theme.TEXT_PRIMARY};
            }}
        """)
        self._activity_list.setMinimumHeight(120)
        body_lay.addWidget(self._activity_list)

        body_lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

    # ── public API ───────────────────────────────────────────────────

    def set_services(self, *, api_client, clipboard_watcher) -> None:  # type: ignore[override]
        """Inject runtime dependencies from the app orchestrator."""
        self._api_client = api_client
        self._clipboard_watcher = clipboard_watcher

    def set_connection_status(self, connected: bool) -> None:
        if connected:
            self._conn_label.setText("Connected")
            self._conn_label.setStyleSheet(f"color: {theme.ACCENT};")
        else:
            self._conn_label.setText("Offline")
            self._conn_label.setStyleSheet(f"color: {theme.ERROR};")

    def log_activity(self, message: str) -> None:
        """Append a timestamped entry to the activity list."""
        ts = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{ts}]  {message}")
        self._activity_list.insertItem(0, item)
        # cap visible items
        while self._activity_list.count() > 200:
            self._activity_list.takeItem(self._activity_list.count() - 1)

    # ── slots ────────────────────────────────────────────────────────

    @Slot()
    def _on_send_clicked(self) -> None:
        """Grab clipboard text and dispatch to the backend."""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard is None:
            self.log_activity("Clipboard unavailable.")
            return

        text = clipboard.text()
        if not text or not text.strip():
            self.log_activity("Clipboard is empty — nothing to send.")
            return

        self.log_activity(f"Sending: {text[:80]}{'…' if len(text) > 80 else ''}")

        if self._api_client is not None:
            # async send through API client (fire & forget via qasync)
            import asyncio

            async def _dispatch() -> None:
                try:
                    result = await self._api_client.send_clip(text)
                    self._last_label.setText(text[:40] + ("…" if len(text) > 40 else ""))
                    self._last_label.setStyleSheet(f"color: {theme.SENT_BADGE};")
                    self.log_activity("Delivered to backend.")
                except Exception as exc:
                    logger.exception("Send failed: %s", exc)
                    self.log_activity(f"Send failed: {exc}")

            loop = asyncio.get_event_loop()
            loop.create_task(_dispatch())
        else:
            self.log_activity("API client not configured — payload buffered locally.")
