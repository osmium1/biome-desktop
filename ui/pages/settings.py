"""Settings page — user / device configuration.

Layout:
  • Fixed header (page title)
  • Scrollable body with cards:
      – Connectivity (device ID, API base URL)
      – Behaviour (auto-send text, auto-send URLs, SpeedBoost overlay)
      – System status (config path, outbox count)
  • Pinned footer with Save / Reset buttons
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
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


def _card(parent: QWidget | None = None) -> QFrame:
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


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {theme.BORDER};")
    return line


class SettingsPage(QWidget):
    """Settings UI with save / reset / dirty tracking."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._settings_store = None  # injected later
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
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 8, 0)
        body_lay.setSpacing(16)

        # ── Connectivity card ────────────────────────────────────────
        conn_card = _card(body)
        cc = QVBoxLayout(conn_card)
        cc.setContentsMargins(20, 16, 20, 16)
        cc.setSpacing(10)
        cc.addWidget(QLabel("Connectivity"))

        cc.addWidget(QLabel("Device ID"))
        self._device_id = QLineEdit()
        self._device_id.setPlaceholderText("auto-detected from hostname")
        self._device_id.textChanged.connect(self._mark_dirty)
        cc.addWidget(self._device_id)

        cc.addWidget(QLabel("API Base URL"))
        self._api_url = QLineEdit()
        self._api_url.setPlaceholderText("http://localhost:8000")
        self._api_url.textChanged.connect(self._mark_dirty)
        cc.addWidget(self._api_url)

        cc.addWidget(QLabel("Firebase Config Path"))
        fb_row = QHBoxLayout()
        self._firebase_path = QLineEdit()
        self._firebase_path.setPlaceholderText("~/.biome/firebase.json")
        self._firebase_path.textChanged.connect(self._mark_dirty)
        fb_row.addWidget(self._firebase_path)
        browse_btn = QPushButton("Browse…")
        browse_btn.setProperty("class", "secondary")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._on_browse)
        fb_row.addWidget(browse_btn)
        cc.addLayout(fb_row)

        body_lay.addWidget(conn_card)

        # ── Behaviour card ───────────────────────────────────────────
        beh_card = _card(body)
        bc = QVBoxLayout(beh_card)
        bc.setContentsMargins(20, 16, 20, 16)
        bc.setSpacing(10)
        bc.addWidget(QLabel("Behaviour"))

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
        sys_card = _card(body)
        sc = QVBoxLayout(sys_card)
        sc.setContentsMargins(20, 16, 20, 16)
        sc.setSpacing(10)
        sc.addWidget(QLabel("System Status"))

        self._config_path_label = QLabel(f"Config: {Path.home() / '.biome'}")
        self._config_path_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: 12px;")
        sc.addWidget(self._config_path_label)

        self._outbox_label = QLabel("Outbox: 0 pending items")
        self._outbox_label.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: 12px;")
        sc.addWidget(self._outbox_label)

        test_btn = QPushButton("Test Connection")
        test_btn.setProperty("class", "secondary")
        test_btn.clicked.connect(self._on_test)
        sc.addWidget(test_btn)

        body_lay.addWidget(sys_card)
        body_lay.addStretch()

        scroll.setWidget(body)
        root.addWidget(scroll, stretch=1)

        # ── footer ───────────────────────────────────────────────────
        root.addSpacing(12)
        footer = QHBoxLayout()
        footer.addStretch()

        self._reset_btn = QPushButton("Reset")
        self._reset_btn.setProperty("class", "secondary")
        self._reset_btn.setFixedWidth(100)
        self._reset_btn.clicked.connect(self._on_reset)
        footer.addWidget(self._reset_btn)

        self._save_btn = QPushButton("Save")
        self._save_btn.setFixedWidth(100)
        self._save_btn.clicked.connect(self._on_save)
        footer.addWidget(self._save_btn)

        root.addLayout(footer)

    # ── public API ───────────────────────────────────────────────────

    def set_settings_store(self, store) -> None:  # type: ignore[override]
        """Inject the settings store and populate fields."""
        self._settings_store = store
        self._load_from_store()

    # ── private ──────────────────────────────────────────────────────

    def _load_from_store(self) -> None:
        if not self._settings_store:
            return
        s = self._settings_store

        # block signals to avoid marking dirty during load
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
        """Quick health-check against the configured backend."""
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
