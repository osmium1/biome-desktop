"""Firebase-backed transport layer."""

from __future__ import annotations

import json
import logging
import os
import platform
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from ..payloads.classifier import Payload
from .config import FirebaseConfig, find_config


SCOPES = [
    "https://www.googleapis.com/auth/devstorage.read_write",
    "https://www.googleapis.com/auth/datastore",
    "https://www.googleapis.com/auth/firebase.messaging",
]

logger = logging.getLogger(__name__)


@dataclass
class FirebaseTransport:
    """Stub transport that spools payloads until Firebase config exists.

    We persist outgoing payloads to `~/.biome/outbox` so nothing is lost
    while the actual Firebase integration (auth, Storage upload, FCM
    notify) is being wired up. Once the config file is populated, this
    class will send the payload over HTTPS; until then we log to the
    outbox for manual inspection.
    """

    config_path: Path = Path.home() / ".biome" / "firebase.json"
    outbox_path: Path = Path.home() / ".biome" / "outbox"
    _session: Any = field(default=None, init=False, repr=False)
    _config: Optional[FirebaseConfig] = field(default=None, init=False, repr=False)
    _credentials: Optional[service_account.Credentials] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.outbox_path.mkdir(parents=True, exist_ok=True)
        self.reload_config()

    @property
    def is_configured(self) -> bool:
        return self._config is not None

    def send(self, payload: Payload, *, raise_on_error: bool = False) -> Optional[dict[str, str]]:
        if not self.is_configured:
            self._write_outbox(payload, reason="firebase-config-missing")
            if raise_on_error:
                raise RuntimeError("firebase config missing")
            return None

        config = self._config
        if not config:
            self._write_outbox(payload, reason="firebase-config-unavailable")
            if raise_on_error:
                raise RuntimeError("firebase config unavailable")
            return None

        if not isinstance(payload.data, str):
            # Binary/mixed payloads still need richer handling.
            self._write_outbox(payload, reason="unsupported-payload-type")
            if raise_on_error:
                raise ValueError("payload type not supported yet")
            return None

        try:
            access_token = self._get_access_token()
            account_id = self._resolve_account_id()
            device_id = self._resolve_device_id()
            clip_id = uuid.uuid4().hex
            storage_path = f"clips/{account_id}/{clip_id}.json"

            upload_meta = self._upload_payload(
                access_token=access_token,
                bucket=config.web.storage_bucket,
                storage_path=storage_path,
                payload=payload,
            )
            self._create_firestore_doc(
                access_token=access_token,
                project_id=config.web.project_id,
                account_id=account_id,
                clip_id=clip_id,
                storage_path=storage_path,
                payload=payload,
                device_id=device_id,
                storage_meta=upload_meta,
            )
            fcm_response = None
            target_token = self._resolve_fcm_token()
            if target_token:
                try:
                    fcm_response = self._send_fcm_message(
                        access_token=access_token,
                        project_id=config.web.project_id,
                        token=target_token,
                        clip_id=clip_id,
                        account_id=account_id,
                        storage_path=storage_path,
                        payload=payload,
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    logger.exception("Unable to send FCM notification: %s", exc)
            result = {
                "account_id": account_id,
                "clip_id": clip_id,
                "storage_path": storage_path,
                "bucket": config.web.storage_bucket,
                "firestore_doc": f"accounts/{account_id}/clips/{clip_id}",
                "fcm_notified": bool(fcm_response),
            }
            logger.info(
                "Uploaded clip %s (%s) -> %s [FCM notified=%s]",
                clip_id,
                payload.kind.name.lower(),
                storage_path,
                bool(fcm_response),
            )
            return result
        except Exception as exc:  # pylint: disable=broad-except
            self._write_outbox(payload, reason=f"firebase-send-error:{exc}")
            if raise_on_error:
                raise
        return None

    def reload_config(self) -> None:
        """Allow runtime refresh after user edits firebase.json."""

        self._config = find_config(self.config_path)
        self._credentials = None
        if self._config:
            info = self._config.service_account.to_google_dict()
            self._credentials = service_account.Credentials.from_service_account_info(
                info, scopes=SCOPES
            )

    # ------------------------------------------------------------------
    # Firebase calls
    # ------------------------------------------------------------------

    def _get_access_token(self) -> str:
        if not self._credentials:
            raise RuntimeError("Firebase credentials not available")
        request = Request()
        self._credentials.refresh(request)
        if not self._credentials.token:
            raise RuntimeError("Unable to retrieve OAuth token")
        return self._credentials.token

    def _upload_payload(
        self,
        *,
        access_token: str,
        bucket: str,
        storage_path: str,
        payload: Payload,
    ) -> dict[str, Any]:
        url = "https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o".format(
            bucket=bucket
        )
        params = {"uploadType": "media", "name": storage_path}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        media = json.dumps(
            {
                "kind": payload.kind.name.lower(),
                "data": payload.data,
                "metadata": payload.metadata,
                "version": 1,
                "sent_at": time.time(),
            }
        )
        response = requests.post(url, headers=headers, params=params, data=media, timeout=15)
        response.raise_for_status()
        return response.json()

    def _create_firestore_doc(
        self,
        *,
        access_token: str,
        project_id: str,
        account_id: str,
        clip_id: str,
        storage_path: str,
        payload: Payload,
        device_id: str,
        storage_meta: dict[str, Any],
    ) -> None:
        url = (
            "https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents/"
            "accounts/{account}/clips?documentId={clip}"
        ).format(project=project_id, account=account_id, clip=clip_id)

        body = {
            "fields": {
                "storagePath": {"stringValue": storage_path},
                "kind": {"stringValue": payload.kind.name.lower()},
                "metadata": {"stringValue": json.dumps(payload.metadata or {})},
                "senderDeviceId": {"stringValue": device_id},
                "status": {"stringValue": "queued"},
                "bucketGeneration": {"stringValue": str(storage_meta.get("generation", ""))},
                "createdAt": {
                    "timestampValue": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                },
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(url, headers=headers, json=body, timeout=15)
        response.raise_for_status()

    def _send_fcm_message(
        self,
        *,
        access_token: str,
        project_id: str,
        token: str,
        clip_id: str,
        account_id: str,
        storage_path: str,
        payload: Payload,
    ) -> dict[str, Any]:
        url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        message = {
            "message": {
                "token": token,
                "data": {
                    "clip_id": clip_id,
                    "account_id": account_id,
                    "kind": payload.kind.name.lower(),
                    "storage_path": storage_path,
                },
            }
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        response = requests.post(url, headers=headers, json=message, timeout=10)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_account_id(self) -> str:
        if self._config:
            return os.environ.get("BIOME_ACCOUNT_ID") or self._config.web.project_id
        return os.environ.get("BIOME_ACCOUNT_ID", "local-dev")

    def _resolve_device_id(self) -> str:
        return os.environ.get("BIOME_DEVICE_ID") or platform.node() or "desktop"

    def _resolve_fcm_token(self) -> Optional[str]:
        token = os.environ.get("BIOME_FCM_DEVICE_TOKEN")
        if token:
            return token.strip()
        return None

    def _write_outbox(self, payload: Payload, reason: str) -> None:
        envelope = {
            "id": str(uuid.uuid4()),
            "reason": reason,
            "timestamp": time.time(),
            "payload": self._serialize_payload(payload),
        }
        target = self.outbox_path / f"{envelope['id']}.json"
        with target.open("w", encoding="utf-8") as handle:
            json.dump(envelope, handle, indent=2)

    def _serialize_payload(self, payload: Payload) -> dict[str, Any]:
        data_repr: Any
        if isinstance(payload.data, str):
            data_repr = payload.data
        else:
            data_repr = repr(payload.data)
        return {
            "kind": payload.kind.name,
            "data": data_repr,
            "metadata": payload.metadata,
        }
