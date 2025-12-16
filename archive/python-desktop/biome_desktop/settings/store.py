"""Local persistence for user/device rules."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..payloads.classifier import Payload, PayloadDecision, PayloadKind


@dataclass
class SettingsStore:
    """Loads and evaluates local settings.

    Eventually this will persist JSON or SQLite records so each device can
    keep its own behavior (auto-send, prompt filters, etc.). For now it
    simply returns default decisions to unblock other modules.
    """

    path: Path = Path.home() / ".biome" / "settings.json"
    _cache: dict[str, Any] | None = None
    _rules: dict[str, Any] = field(default_factory=dict)

    def load(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as handle:
                self._cache = json.load(handle)
        else:
            self._cache = self._default_rules()
            self.save()
        self._rules = self._cache or self._default_rules()

    def should_auto_send(self, payload: Payload) -> PayloadDecision:
        rules = self._rules or self._default_rules()
        if payload.kind == PayloadKind.URL:
            if rules.get("auto_send_urls"):
                return PayloadDecision(send=True)
            return PayloadDecision(send=False, reason="confirm-url")
        if payload.kind == PayloadKind.TEXT:
            if rules.get("auto_send_text"):
                return PayloadDecision(send=True)
            return PayloadDecision(send=False, reason="confirm-text")
        return PayloadDecision(send=False, reason="unsupported-kind")

    def set_rule(self, key: str, value: Any) -> None:
        if self._cache is None:
            self.load()
        self._rules[key] = value
        self._cache = self._rules
        self.save()

    def get_rule(self, key: str, default: Any = None) -> Any:
        if self._cache is None:
            self.load()
        return self._rules.get(key, default)

    def all_rules(self) -> dict[str, Any]:
        if self._cache is None:
            self.load()
        return dict(self._rules)

    def save(self) -> None:
        if self._cache is None:
            return
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._cache, handle, indent=2)

    def _default_rules(self) -> dict[str, Any]:
        return {
            "auto_send_text": False,
            "auto_send_urls": False,
        }
