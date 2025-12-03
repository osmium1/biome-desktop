"""Helpers to normalize clipboard data before transport."""

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


_URL_RE = re.compile(r"^(https?://\S+)$", re.IGNORECASE)


class PayloadClassifier:
    """Inspect clipboard content and tag it with metadata."""

    def classify(self, raw_clipboard: object) -> Optional[Payload]:
        if isinstance(raw_clipboard, str):
            kind = PayloadKind.TEXT
            metadata: dict[str, object] = {"length": len(raw_clipboard)}
            if _URL_RE.match(raw_clipboard.strip()):
                kind = PayloadKind.URL
                metadata["domain"] = self._extract_domain(raw_clipboard)
            return Payload(kind=kind, data=raw_clipboard, metadata=metadata)
        # TODO: add detection for images/files once watcher supports them.
        return None

    def _extract_domain(self, url: str) -> Optional[str]:
        try:
            # Simple heuristic to keep dependencies light for now.
            without_scheme = url.split("//", 1)[-1]
            host = without_scheme.split("/", 1)[0]
            return host.lower()
        except (ValueError, AttributeError):
            return None
