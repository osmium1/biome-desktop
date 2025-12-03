"""Application orchestrator for the Biome desktop client.

At this stage the module wires together the future service objects
(clipboard watcher, classifier, transport, tray UI, settings store) but
keeps the implementation light so we can iterate per module. The intent
is to make dependencies explicit and testable instead of relying on a
single procedural script.
"""

from __future__ import annotations

import logging
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from .clipboard.watcher import ClipboardWatcher
from .payloads.classifier import PayloadClassifier
from .settings.store import SettingsStore
from .transport.firebase_client import FirebaseTransport
from .ui.tray import TrayController


logger = logging.getLogger(__name__)


@dataclass
class BiomeApp:
    """High-level container owning all desktop services."""

    watcher: ClipboardWatcher = field(default_factory=ClipboardWatcher)
    classifier: PayloadClassifier = field(default_factory=PayloadClassifier)
    settings: SettingsStore = field(default_factory=SettingsStore)
    transport: FirebaseTransport = field(default_factory=FirebaseTransport)
    tray: Optional[TrayController] = None

    def __post_init__(self) -> None:
        # Delay tray creation until settings are ready so future UI can
        # reflect account state and device rules.
        self.tray = TrayController(app=self)

    def start(self) -> None:
        """Kick off watchers and show the tray icon."""

        self.settings.load()
        self.watcher.start(on_clipboard_event=self._handle_clipboard_event)
        if self.tray:
            self.tray.run()

    def stop(self) -> None:
        """Stop background services gracefully."""

        self.watcher.stop()
        if self.tray:
            self.tray.stop()

    def _handle_clipboard_event(self, raw_clip: object) -> None:
        """Process clipboard updates coming from the watcher."""

        payload = self.classifier.classify(raw_clip)
        if not payload:
            return

        auto_sent = False
        decision = self.settings.should_auto_send(payload)
        if decision.send:
            try:
                self.transport.send(payload)
                auto_sent = True
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("Failed to auto-send clipboard payload: %s", exc)
                auto_sent = False

        if self.tray:
            self.tray.handle_clipboard_buffer(payload, auto_sent=auto_sent, reason=decision.reason)


def run() -> None:
    """Convenience entry point used by `main.py`."""

    _configure_logging()
    app = BiomeApp()
    app.start()


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    level_name = os.environ.get("BIOME_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
