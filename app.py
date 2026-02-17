"""Application orchestrator — wires all services together.

Creates the QApplication, applies the theme, builds the main window,
starts the tray, clipboard watcher, and integrates qasync for async
HTTP calls.  This is the single composition root for the desktop client.
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import sys


logger = logging.getLogger(__name__)


def run() -> None:
    """Entry point — initialise Qt + async loop and launch the app."""

    _configure_logging()

    # ── Qt application ───────────────────────────────────────────────
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("Biome")
    app.setOrganizationName("Biome")
    app.setQuitOnLastWindowClosed(False)  # keep alive in tray

    # ── theme ────────────────────────────────────────────────────────
    from ui.theme import apply_theme
    apply_theme(app)

    # ── async event loop (qasync) ────────────────────────────────────
    import qasync
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # ── settings ─────────────────────────────────────────────────────
    from settings.store import SettingsStore
    settings = SettingsStore()
    settings.load()

    # ── API client ───────────────────────────────────────────────────
    from api.client import BiomeApiClient
    api_base = settings.get("api_base_url", "http://localhost:8000")
    api_client = BiomeApiClient(base_url=api_base)

    # ── clipboard watcher ────────────────────────────────────────────
    from clipboard.watcher import ClipboardWatcher
    clipboard_watcher = ClipboardWatcher()

    # ── payload classifier ───────────────────────────────────────────
    from payloads.classifier import PayloadClassifier
    classifier = PayloadClassifier()

    # ── overlay ──────────────────────────────────────────────────────
    from ui.overlay import SpeedBoostOverlay
    overlay = SpeedBoostOverlay()

    # ── main window ──────────────────────────────────────────────────
    from ui.main_window import MainWindow
    window = MainWindow()
    window.dashboard_page.set_services(
        api_client=api_client,
        clipboard_watcher=clipboard_watcher,
    )
    window.settings_page.set_settings_store(settings)

    # ── tray service ─────────────────────────────────────────────────
    from tray.service import TrayService, TrayState
    tray = TrayService()

    def _on_tray_show() -> None:
        window.show()
        window.raise_()
        window.activateWindow()

    tray.show_requested.connect(_on_tray_show)
    tray.quit_requested.connect(app.quit)

    # Send from tray menu
    def _on_tray_send() -> None:
        cb = app.clipboard()
        if cb is None:
            return
        text = cb.text()
        if not text or not text.strip():
            tray.notify("Biome", "Clipboard is empty.")
            return

        async def _dispatch() -> None:
            tray.set_state(TrayState.SENDING)
            if settings.get("speedboost_enabled", True):
                overlay.start()
            try:
                await api_client.send_clip(text)
                tray.set_state(TrayState.SENT)
                tray.notify("Biome", "Clipboard sent.")
                window.dashboard_page.log_activity(f"Sent: {text[:60]}…")
            except Exception as exc:
                logger.exception("Tray send failed: %s", exc)
                tray.set_state(TrayState.ERROR)
                tray.notify("Biome", f"Send failed: {exc}")
            finally:
                overlay.stop()
                # return to idle after a brief pause
                from PySide6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: tray.set_state(TrayState.IDLE))

        asyncio.get_event_loop().create_task(_dispatch())

    tray.send_requested.connect(_on_tray_send)

    # ── clipboard auto-send wiring ───────────────────────────────────
    def _on_clipboard_captured(text: str) -> None:
        payload = classifier.classify(text)
        if payload is None:
            return

        from payloads.classifier import PayloadKind
        auto_send = False
        if payload.kind == PayloadKind.TEXT and settings.get("auto_send_text"):
            auto_send = True
        elif payload.kind == PayloadKind.URL and settings.get("auto_send_urls"):
            auto_send = True

        if auto_send:

            async def _auto() -> None:
                tray.set_state(TrayState.SENDING)
                if settings.get("speedboost_enabled", True):
                    overlay.start()
                try:
                    await api_client.send_clip(text)
                    tray.set_state(TrayState.SENT)
                    window.dashboard_page.log_activity(f"Auto-sent: {text[:60]}")
                except Exception as exc:
                    logger.exception("Auto-send failed: %s", exc)
                    tray.set_state(TrayState.ERROR)
                finally:
                    overlay.stop()
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(2000, lambda: tray.set_state(TrayState.IDLE))

            asyncio.get_event_loop().create_task(_auto())
        else:
            tray.set_state(TrayState.WAITING)
            window.dashboard_page.log_activity(f"Clipboard captured: {text[:60]}")

    clipboard_watcher.text_captured.connect(_on_clipboard_captured)

    # ── health check on startup ──────────────────────────────────────
    async def _initial_health() -> None:
        ok = await api_client.health_check()
        window.dashboard_page.set_connection_status(ok)
        if ok:
            window.dashboard_page.log_activity("Backend connected.")
        else:
            window.dashboard_page.log_activity("Backend unreachable — payloads will queue locally.")

    # ── launch ───────────────────────────────────────────────────────
    clipboard_watcher.start()
    tray.show()
    window.show()

    with loop:
        loop.create_task(_initial_health())
        loop.run_forever()


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    level_name = os.environ.get("BIOME_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
