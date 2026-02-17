"""Dashboard page — primary clipboard-send console.

Layout (top → bottom):
  - Page heading + subheading
  - "Clipboard Dispatch" card with send button
  - Status cards row (connection, last sent)
  - Activity log
"""

from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGroupBox,
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


class DashboardPage(QWidget):
    """Console / home page shown after app launch."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

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
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(16)

        # ── send card ────────────────────────────────────────────────
        send_card = QGroupBox("Clipboard Dispatch")
        sc_lay = QVBoxLayout(send_card)
        sc_lay.setSpacing(12)

        send_desc = QLabel("Grab the current system clipboard and push it to all linked devices.")
        send_desc.setProperty("class", "card-value")
        send_desc.setWordWrap(True)
        sc_lay.addWidget(send_desc)

        self._send_btn = QPushButton("  Send Clipboard")
        self._send_btn.setProperty("class", "primary")
        self._send_btn.setIcon(QIcon(theme.icon_path("send")))
        self._send_btn.setFixedHeight(42)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.clicked.connect(self._on_send_clicked)
        sc_lay.addWidget(self._send_btn)

        body_lay.addWidget(send_card)

        # ── status cards row ─────────────────────────────────────────
        row = QHBoxLayout()
        row.setSpacing(12)

        # connection card
        conn_card = QGroupBox("Connection")
        cc_lay = QVBoxLayout(conn_card)
        self._conn_label = QLabel("Checking…")
        self._conn_label.setProperty("class", "card-value")
        cc_lay.addWidget(self._conn_label)
        conn_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(conn_card)

        # last sent card
        last_card = QGroupBox("Last Sent")
        lc_lay = QVBoxLayout(last_card)
        self._last_label = QLabel("Nothing yet")
        self._last_label.setProperty("class", "card-value")
        lc_lay.addWidget(self._last_label)
        last_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(last_card)

        body_lay.addLayout(row)

        # ── activity log ─────────────────────────────────────────────
        log_header = QLabel("Activity")
        log_header.setProperty("class", "card-title")
        body_lay.addWidget(log_header)

        self._activity_list = QListWidget()
        self._activity_list.setMinimumHeight(140)
        body_lay.addWidget(self._activity_list)

        body_lay.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

    # ── public API ───────────────────────────────────────────────────

    def set_services(self, *, api_client, clipboard_watcher) -> None:
        self._api_client = api_client
        self._clipboard_watcher = clipboard_watcher

    def set_connection_status(self, connected: bool) -> None:
        if connected:
            self._conn_label.setText("● Connected")
            self._conn_label.setStyleSheet(f"color: {theme.ACCENT};")
        else:
            self._conn_label.setText("● Offline")
            self._conn_label.setStyleSheet(f"color: {theme.ERROR};")

    def log_activity(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"[{ts}]  {message}")
        self._activity_list.insertItem(0, item)
        while self._activity_list.count() > 200:
            self._activity_list.takeItem(self._activity_list.count() - 1)

    # ── slots ────────────────────────────────────────────────────────

    @Slot()
    def _on_send_clicked(self) -> None:
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
            import asyncio

            async def _dispatch() -> None:
                try:
                    await self._api_client.send_clip(text)
                    self._last_label.setText(text[:40] + ("…" if len(text) > 40 else ""))
                    self._last_label.setStyleSheet(f"color: {theme.SENT_BADGE};")
                    self.log_activity("Delivered to backend.")
                except Exception as exc:
                    logger.exception("Send failed: %s", exc)
                    self.log_activity(f"Send failed: {exc}")

            asyncio.get_event_loop().create_task(_dispatch())
        else:
            self.log_activity("API client not configured — payload buffered locally.")
