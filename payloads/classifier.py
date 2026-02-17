"""Payload classification — port of the legacy classifier.

Tags clipboard content as TEXT, URL, IMAGE, or FILE and attaches
lightweight metadata.  Consumed by the tray auto-send logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class PayloadKind(Enum):
    TEXT = auto()
    URL = auto()
    IMAGE = auto()
    FILE = auto()


@dataclass
class Payload:
    kind: PayloadKind
    data: object
    metadata: dict[str, object]


@dataclass
class PayloadDecision:
    send: bool
    reason: str | None = None


_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


class PayloadClassifier:
    """Classify raw clipboard data into a typed Payload."""

    def classify(self, raw: object) -> Optional[Payload]:
        if isinstance(raw, str):
            text = raw.strip()
            if not text:
                return None
            kind = PayloadKind.TEXT
            meta: dict[str, object] = {"length": len(text)}
            if _URL_RE.match(text):
                kind = PayloadKind.URL
                meta["domain"] = self._extract_domain(text)
            return Payload(kind=kind, data=text, metadata=meta)
        return None

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        try:
            without_scheme = url.split("//", 1)[-1]
            return without_scheme.split("/", 1)[0].lower()
        except (ValueError, AttributeError):
            return None
