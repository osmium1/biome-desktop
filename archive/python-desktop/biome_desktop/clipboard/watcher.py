"""Clipboard watching utilities."""

from __future__ import annotations

import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from typing import Callable, Optional

Callback = Callable[[object], None]


@dataclass
class ClipboardWatcher:
    """Best-effort clipboard poller for Windows-only MVP.

    We rely on a lightweight `tkinter` clipboard read to avoid pulling in
    heavier native dependencies (pywin32) until we need richer payloads
    like images or file drops. The poller runs on a background thread to
    keep the tray UI responsive.
    """

    poll_interval: float = 0.75
    _callback: Optional[Callback] = None
    _running: bool = False
    _thread: Optional[threading.Thread] = None
    _last_fingerprint: str | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def start(self, on_clipboard_event: Callback) -> None:
        if self._running:
            return
        self._callback = on_clipboard_event
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._callback = None
        self._last_fingerprint = None

    def _loop(self) -> None:
        while self._running:
            value = self._read_clipboard()
            if value is not None:
                fingerprint = self._fingerprint(value)
                if fingerprint != self._last_fingerprint:
                    self._last_fingerprint = fingerprint
                    self._emit(value)
            time.sleep(self.poll_interval)

    def _read_clipboard(self) -> Optional[str]:
        # Each call creates its own Tk root to avoid dealing with the
        # global mainloop. This is fast enough for small polling
        # intervals and keeps dependencies minimal.
        root = tk.Tk()
        root.withdraw()
        try:
            data = root.clipboard_get()
            return data if isinstance(data, str) else None
        except tk.TclError:
            return None
        finally:
            root.destroy()

    def _fingerprint(self, value: object) -> str:
        return f"{type(value).__name__}:{hash(value)}"

    def _emit(self, raw_value: object) -> None:
        with self._lock:
            callback = self._callback
        if callback and self._running:
            callback(raw_value)
