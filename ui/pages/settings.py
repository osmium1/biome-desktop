"""Settings page — user / device configuration.

Layout:
  - Fixed header (page title)
  - Scrollable body with QGroupBox cards:
      – Connectivity (device ID, API base URL, Firebase config)
      – Behaviour (auto-send toggles, SpeedBoost option)
      – System Status (config path, outbox count, test button)
  - Pinned footer with Save / Reset buttons
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import theme

logger = logging.getLogger(__name__)


class SettingsPage(QWidget):
    """Settings UI with save / reset / dirty tracking."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._settings_store = None
        self._dirty = False

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 16)
        root.setSpacing(0)

        # ── header ───────────────────────────────────────────────────
        heading = QLabel("Settings")
        heading.setProperty("class", "heading")
        root.addWidget(heading)

        sub = QLabel("Configure device behaviour and connectivity.")
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
        body_lay.setContentsMargins(0, 0, 8, 0)
        body_lay.setSpacing(16)

        # ── Connectivity card ────────────────────────────────────────
        conn_card = QGroupBox("Connectivity")
        cc = QFormLayout(conn_card)
        cc.setSpacing(10)
        cc.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._device_id = QLineEdit()
        self._device_id.setPlaceholderText("auto-detected from hostname")
        self._device_id.textChanged.connect(self._mark_dirty)
        cc.addRow("Device ID", self._device_id)

        self._api_url = QLineEdit()
        self._api_url.setPlaceholderText("http://localhost:8000")
        self._api_url.textChanged.connect(self._mark_dirty)
        cc.addRow("API Base URL", self._api_url)

        fb_row = QHBoxLayout()
        self._firebase_path = QLineEdit()
        self._firebase_path.setPlaceholderText("~/.biome/firebase.json")
        self._firebase_path.textChanged.connect(self._mark_dirty)
        fb_row.addWidget(self._firebase_path)
        browse_btn = QPushButton("  Browse…  ")
        browse_btn.setProperty("class", "secondary")
        browse_btn.setMinimumWidth(100)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._on_browse)
        fb_row.addWidget(browse_btn)
        cc.addRow("Firebase Config", fb_row)

        body_lay.addWidget(conn_card)

        # ── Behaviour card ───────────────────────────────────────────
        beh_card = QGroupBox("Behaviour")
        bc = QVBoxLayout(beh_card)
        bc.setSpacing(10)

        self._auto_text = QCheckBox("Auto-send plain text")
        self._auto_text.toggled.connect(self._mark_dirty)
        bc.addWidget(self._auto_text)

        self._auto_urls = QCheckBox("Auto-send URLs")
        self._auto_urls.toggled.connect(self._mark_dirty)
        bc.addWidget(self._auto_urls)

        self._speedboost = QCheckBox("SpeedBoost overlay animation")
        self._speedboost.toggled.connect(self._mark_dirty)
        bc.addWidget(self._speedboost)

        body_lay.addWidget(beh_card)

        # ── System card ──────────────────────────────────────────────
        sys_card = QGroupBox("System Status")
        sc = QVBoxLayout(sys_card)
        sc.setSpacing(10)

        self._config_path_label = QLabel(f"Config: {Path.home() / '.biome'}")
        self._config_path_label.setProperty("class", "card-value")
        sc.addWidget(self._config_path_label)

        self._outbox_label = QLabel("Outbox: 0 pending items")
        self._outbox_label.setProperty("class", "card-value")
        sc.addWidget(self._outbox_label)

        test_btn = QPushButton("Test Connection")
        test_btn.setProperty("class", "secondary")
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._on_test)
        sc.addWidget(test_btn)

        body_lay.addWidget(sys_card)
        body_lay.addStretch()

        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        # ── footer ───────────────────────────────────────────────────
        footer_widget = QWidget()
        footer_widget.setObjectName("footer_bar")
        footer_widget.setFixedHeight(56)
        footer = QHBoxLayout(footer_widget)
        footer.setContentsMargins(24, 8, 24, 8)
        footer.addStretch()

        self._reset_btn = QPushButton("Reset")
        self._reset_btn.setProperty("class", "secondary")
        self._reset_btn.setFixedWidth(100)
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.clicked.connect(self._on_reset)
        footer.addWidget(self._reset_btn)

        self._save_btn = QPushButton("Save")
        self._save_btn.setProperty("class", "primary")
        self._save_btn.setFixedWidth(100)
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.clicked.connect(self._on_save)
        footer.addWidget(self._save_btn)

        root.addWidget(footer_widget)

    # ── public API ───────────────────────────────────────────────────

    def set_settings_store(self, store) -> None:
        self._settings_store = store
        self._load_from_store()

    # ── private ──────────────────────────────────────────────────────

    def _load_from_store(self) -> None:
        if not self._settings_store:
            return
        s = self._settings_store

        for w in (self._device_id, self._api_url, self._firebase_path,
                  self._auto_text, self._auto_urls, self._speedboost):
            w.blockSignals(True)

        self._device_id.setText(s.get("device_id", ""))
        self._api_url.setText(s.get("api_base_url", "http://localhost:8000"))
        self._firebase_path.setText(s.get("firebase_config_path", ""))
        self._auto_text.setChecked(s.get("auto_send_text", False))
        self._auto_urls.setChecked(s.get("auto_send_urls", False))
        self._speedboost.setChecked(s.get("speedboost_enabled", True))

        for w in (self._device_id, self._api_url, self._firebase_path,
                  self._auto_text, self._auto_urls, self._speedboost):
            w.blockSignals(False)

        self._dirty = False
        self._update_outbox_count()

    def _gather_values(self) -> dict:
        return {
            "device_id": self._device_id.text().strip(),
            "api_base_url": self._api_url.text().strip() or "http://localhost:8000",
            "firebase_config_path": self._firebase_path.text().strip(),
            "auto_send_text": self._auto_text.isChecked(),
            "auto_send_urls": self._auto_urls.isChecked(),
            "speedboost_enabled": self._speedboost.isChecked(),
        }

    def _update_outbox_count(self) -> None:
        outbox = Path.home() / ".biome" / "outbox"
        count = len(list(outbox.glob("*.json"))) if outbox.exists() else 0
        self._outbox_label.setText(f"Outbox: {count} pending item{'s' if count != 1 else ''}")

    @Slot()
    def _mark_dirty(self) -> None:
        self._dirty = True

    @Slot()
    def _on_save(self) -> None:
        if self._settings_store is None:
            return
        values = self._gather_values()
        for k, v in values.items():
            self._settings_store.set(k, v)
        self._settings_store.save()
        self._dirty = False
        logger.info("Settings saved.")

    @Slot()
    def _on_reset(self) -> None:
        self._load_from_store()

    @Slot()
    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select firebase.json", str(Path.home()),
            "JSON files (*.json);;All files (*)",
        )
        if path:
            self._firebase_path.setText(path)

    @Slot()
    def _on_test(self) -> None:
        if self._api_client is None:
            logger.warning("No API client to test.")
            return

        import asyncio

        async def _check() -> None:
            try:
                ok = await self._api_client.health_check()
                if ok:
                    self._conn_status = "ok"
                else:
                    self._conn_status = "fail"
            except Exception as exc:
                logger.exception("Health check failed: %s", exc)

        asyncio.get_event_loop().create_task(_check())
