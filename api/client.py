"""Async HTTP client for the Biome backend API.

Wraps ``httpx.AsyncClient`` to provide typed methods for the two core
endpoints: ``POST /api/clips`` and ``GET /api/health``.  The client is
designed to work inside the qasync event loop.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class BiomeApiClient:
    """Lightweight async wrapper around the Biome REST API."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self._base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=15.0,
                headers={"User-Agent": "BiomeDesktop/0.1"},
            )
        return self._client

    # ── endpoints ────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Return True if the backend is reachable and healthy."""
        try:
            client = await self._ensure_client()
            resp = await client.get("/api/health")
            return resp.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning("Health check failed: %s", exc)
            return False

    async def send_clip(self, text: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Post a clipboard payload to the backend.

        Returns the JSON response body on success, raises on failure.
        """
        client = await self._ensure_client()
        body: dict[str, Any] = {
            "kind": "text",
            "data": text,
        }
        if metadata:
            body["metadata"] = metadata

        resp = await client.post("/api/clips", json=body)
        resp.raise_for_status()
        return resp.json()

    # ── lifecycle ────────────────────────────────────────────────────

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
