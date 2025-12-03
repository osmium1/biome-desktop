"""Simple Tk-based configuration dialog."""

from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Optional

from ..settings.store import SettingsStore


class ConfigDialog:
    """Modal-ish window for local device rules."""

    def __init__(self, settings: SettingsStore, outbox_path: Path) -> None:
        self._settings = settings
        self._outbox_path = outbox_path
        self._root: Optional[tk.Tk] = None
        self._auto_text: Optional[tk.BooleanVar] = None
        self._auto_urls: Optional[tk.BooleanVar] = None

    def show(self) -> None:
        if self._root and self._root.winfo_exists():
            self._root.deiconify()
            self._root.lift()
            return

        self._root = tk.Tk()
        self._root.title("Biome Settings")
        self._root.resizable(False, False)

        self._auto_text = tk.BooleanVar(master=self._root, value=bool(self._settings.get_rule("auto_send_text")))
        self._auto_urls = tk.BooleanVar(master=self._root, value=bool(self._settings.get_rule("auto_send_urls")))

        ttk.Label(self._root, text="Auto-send rules", font=("Segoe UI", 12, "bold")).pack(
            padx=16, pady=(16, 8)
        )
        ttk.Checkbutton(
            self._root,
            text="Send plain text without prompting",
            variable=self._auto_text,
            command=lambda: self._apply_change("auto_send_text", self._auto_text.get()),
        ).pack(anchor="w", padx=24)
        ttk.Checkbutton(
            self._root,
            text="Send URLs without prompting",
            variable=self._auto_urls,
            command=lambda: self._apply_change("auto_send_urls", self._auto_urls.get()),
        ).pack(anchor="w", padx=24, pady=(0, 12))

        ttk.Separator(self._root, orient="horizontal").pack(fill="x", padx=16, pady=8)

        ttk.Label(
            self._root,
            text="Diagnostics",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=16)
        ttk.Button(
            self._root,
            text="Open Outbox Folder",
            command=self._open_outbox,
        ).pack(anchor="w", padx=24, pady=(4, 8))

        ttk.Button(self._root, text="Close", command=self._close).pack(pady=(8, 16))
        self._root.protocol("WM_DELETE_WINDOW", self._close)
        self._root.mainloop()

    def _apply_change(self, key: str, value: bool) -> None:
        self._settings.set_rule(key, bool(value))

    def _open_outbox(self) -> None:
        self._outbox_path.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(self._outbox_path)
        except OSError:
            pass

    def _close(self) -> None:
        if self._root:
            self._root.destroy()
            self._root = None
            self._auto_text = None
            self._auto_urls = None