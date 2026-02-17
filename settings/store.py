"""Local settings persistence.

Stores user preferences as JSON at ``~/.biome/appsettings.user.json``.
This mirrors the C# ``UserSettingsStore`` and the legacy Python
``SettingsStore``, but is simplified to a flat key→value dict.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULTS: dict[str, Any] = {
    "device_id": "",
    "api_base_url": "http://localhost:8000",
    "firebase_config_path": "",
    "auto_send_text": False,
    "auto_send_urls": False,
    "speedboost_enabled": True,
}


class SettingsStore:
    """Read/write JSON settings at ``~/.biome/appsettings.user.json``."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (Path.home() / ".biome" / "appsettings.user.json")
        self._data: dict[str, Any] = dict(_DEFAULTS)

    # ── lifecycle ────────────────────────────────────────────────────

    def load(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            try:
                with self._path.open("r", encoding="utf-8") as f:
                    on_disk = json.load(f)
                # merge on-disk values over defaults
                self._data = {**_DEFAULTS, **on_disk}
                logger.info("Settings loaded from %s", self._path)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load settings: %s — using defaults", exc)
                self._data = dict(_DEFAULTS)
        else:
            self._data = dict(_DEFAULTS)
            self.save()
            logger.info("Created default settings at %s", self._path)

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
        logger.debug("Settings saved.")

    # ── accessors ────────────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def all(self) -> dict[str, Any]:
        return dict(self._data)
