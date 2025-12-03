"""System tray UI controller."""

from __future__ import annotations

import base64
import logging
import mimetypes
import threading
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog
from typing import TYPE_CHECKING, Optional

from PIL import Image
import pystray
from pystray import MenuItem

if TYPE_CHECKING:
    from ..app import BiomeApp

from ..payloads.classifier import PayloadKind, Payload
from .config_dialog import ConfigDialog


@dataclass
class TrayController:
    """Owns the tray icon, menus, and prompts."""

    app: "BiomeApp"
    _icon: Optional[pystray.Icon] = field(default=None, init=False)
    _icon_image: Optional[Image.Image] = field(default=None, init=False)
    _last_payload: Optional[Payload] = field(default=None, init=False)
    _config_dialog: Optional[ConfigDialog] = field(default=None, init=False)
    _icon_title_idle: str = field(default="Biome", init=False)
    _icon_title_pending: str = field(default="Biome – clipboard ready", init=False)
    _icons: dict[str, Image.Image] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._icons = self._load_icons()
        self._icon_image = self._icons.get("idle")
        self._config_dialog = ConfigDialog(
            settings=self.app.settings,
            outbox_path=self.app.transport.outbox_path,
        )

    def run(self) -> None:
        menu = pystray.Menu(
            MenuItem(
                "Send clipboard to Biome",
                self._menu_send_last,
                enabled=lambda item: self._last_payload is not None,
                default=True,
            ),
            MenuItem("Share image…", self._menu_share_image),
            MenuItem("Config", self._menu_config),
            MenuItem("Exit", self._menu_exit),
        )
        self._icon = pystray.Icon("Biome", self._icon_image, self._icon_title_idle, menu,)
        self._icon.run()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()
            self._icon = None

    def handle_clipboard_buffer(self, payload: Payload, *, auto_sent: bool, reason: str | None = None) -> None:
        """Record clipboard data and update tray indicators."""

        self._last_payload = payload
        if auto_sent:
            self._set_icon_state("idle")
            self._notify_icon("Clipboard sent to Biome automatically.")
            return

        self._set_icon_state("waiting")
        message = "Clipboard captured. Click ‘Send clipboard to Biome’ when ready."
        if reason:
            message += f" (Reason: {reason})"
        self._notify_icon(message)

    # ------------------------------------------------------------------
    # Menu callbacks
    # ------------------------------------------------------------------

    def _menu_send_last(self, icon: pystray.Icon, item: MenuItem) -> None:
        if not self._last_payload:
            self._notify_icon("No clipboard data yet.")
            return
        self._send_payload(self._last_payload)

    def _menu_share_image(self, icon: pystray.Icon, item: MenuItem) -> None:
        path = self._prompt_image_path()
        if not path:
            return
        payload = self._build_image_payload(path)
        if not payload:
            self._notify_icon("Could not load the selected image.")
            return
        self._send_payload(payload)

    def _menu_config(self, icon: pystray.Icon, item: MenuItem) -> None:
        if not self._config_dialog:
            self._notify_icon("Settings dialog unavailable.")
            return
        threading.Thread(target=self._config_dialog.show, daemon=True).start()

    def _menu_exit(self, icon: pystray.Icon, item: MenuItem) -> None:
        self.app.stop()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _payload_preview(self, payload: Payload) -> str:
        if isinstance(payload.data, str):
            snippet = payload.data.strip().replace("\n", " ")
            return snippet[:140] + ("…" if len(snippet) > 140 else "")
        return repr(payload.data)

    def _load_icons(self) -> dict[str, Image.Image]:
        repo_root = Path(__file__).resolve().parents[2]
        search_paths = [
            repo_root / "images",
            repo_root / "legacy" / "images",
        ]
        variants = {
            "idle": "icon-128-green.png",
            "waiting": "icon-128-red.png",
            "sending": "icon-128-yellow.png",
            "sent": "icon-128-white.png",
        }
        icons: dict[str, Image.Image] = {}
        for state, filename in variants.items():
            for base in search_paths:
                icon_path = base / filename
                if icon_path.exists():
                    icons[state] = Image.open(icon_path)
                    break
            else:
                logging.warning("Tray icon variant missing: %s", filename)
        if "idle" not in icons:
            raise FileNotFoundError("Idle tray icon missing; expected icon-128-green.png")
        return icons

    def _send_payload(self, payload: Payload) -> None:
        threading.Thread(
            target=self._send_payload_async,
            args=(payload,),
            daemon=True,
        ).start()

    def _send_payload_async(self, payload: Payload) -> None:
        try:
            self._set_icon_state("sending")
            self._notify_icon("Sending clipboard to Biome…")
            self.app.transport.send(payload)
            self._set_icon_state("sent")
            if payload.kind == PayloadKind.IMAGE:
                self._notify_icon("Image queued for delivery.")
            else:
                self._notify_icon("Clipboard item queued for delivery.")
        except Exception as exc:  # pylint: disable=broad-except
            logging.exception("Failed to send payload: %s", exc)
            self._notify_icon(f"Failed to send payload: {exc}")
        finally:
            self._set_icon_state("idle")

    def _prompt_image_path(self) -> Optional[Path]:
        root = tk.Tk()
        root.withdraw()
        try:
            selection = filedialog.askopenfilename(
                title="Select image to share",
                filetypes=[
                    ("Images", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                    ("All files", "*.*"),
                ],
                parent=root,
            )
        finally:
            root.destroy()
        if not selection:
            return None
        return Path(selection)

    def _build_image_payload(self, path: Path) -> Optional[Payload]:
        if not path.exists() or not path.is_file():
            return None
        data = path.read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        mimetype, _ = mimetypes.guess_type(path.name)
        return Payload(
            kind=PayloadKind.IMAGE,
            data=encoded,
            metadata={
                "filename": path.name,
                "mimetype": mimetype or "application/octet-stream",
                "encoding": "base64",
                "size_bytes": len(data),
            },
        )

    def _set_icon_state(self, state: str) -> None:
        if not self._icon:
            return
        if state == "waiting":
            self._icon.title = self._icon_title_pending
        else:
            self._icon.title = self._icon_title_idle
        icon_image = self._icons.get(state) or self._icons.get("idle")
        if icon_image:
            try:
                self._icon.icon = icon_image
            except Exception:
                logging.debug("Failed to update tray icon for state %s", state)

    def _notify_icon(self, message: str) -> None:
        if self._icon:
            try:
                self._icon.notify(message)
                return
            except NotImplementedError:
                pass
        logging.info("Tray: %s", message)
