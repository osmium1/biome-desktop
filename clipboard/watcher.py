"""Clipboard watcher using QClipboard.

Unlike the legacy tkinter poller, PySide6's QClipboard emits a
``dataChanged`` signal natively — no background thread needed.  The
watcher must be created on the main (GUI) thread because QClipboard
requires an active QApplication.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

ClipboardCallback = Callable[[str], None]


class ClipboardWatcher(QObject):
    """Watches for clipboard text changes and emits ``text_captured``.

    Signals
    -------
    text_captured(str)
        Fired whenever the clipboard text changes.
    """

    text_captured = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._last_text: str = ""
        self._enabled: bool = False
        self._clipboard = None

    def start(self) -> None:
        """Begin monitoring clipboard changes."""
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication must exist before starting ClipboardWatcher")
        self._clipboard = app.clipboard()
        self._clipboard.dataChanged.connect(self._on_data_changed)
        self._enabled = True
        logger.info("ClipboardWatcher started.")

    def stop(self) -> None:
        """Stop monitoring."""
        self._enabled = False
        if self._clipboard is not None:
            try:
                self._clipboard.dataChanged.disconnect(self._on_data_changed)
            except RuntimeError:
                pass
        logger.info("ClipboardWatcher stopped.")

    @Slot()
    def _on_data_changed(self) -> None:
        if not self._enabled or self._clipboard is None:
            return
        text = self._clipboard.text()
        if not text or text == self._last_text:
            return
        self._last_text = text
        logger.debug("Clipboard changed: %s", text[:60])
        self.text_captured.emit(text)
