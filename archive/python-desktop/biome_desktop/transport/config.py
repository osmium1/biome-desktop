"""Helpers for loading Firebase configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class WebConfig:
    api_key: str
    auth_domain: str
    project_id: str
    storage_bucket: str
    messaging_sender_id: str
    app_id: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebConfig":
        required = [
            "apiKey",
            "authDomain",
            "projectId",
            "storageBucket",
            "messagingSenderId",
            "appId",
        ]
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"web config missing fields: {missing}")
        return cls(
            api_key=data["apiKey"],
            auth_domain=data["authDomain"],
            project_id=data["projectId"],
            storage_bucket=data["storageBucket"],
            messaging_sender_id=data["messagingSenderId"],
            app_id=data["appId"],
        )


@dataclass
class ServiceAccount:
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    token_uri: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceAccount":
        required = [
            "project_id",
            "private_key_id",
            "private_key",
            "client_email",
            "client_id",
            "token_uri",
        ]
        missing = [field for field in required if field not in data]
        if missing:
            raise ValueError(f"service account config missing fields: {missing}")
        return cls(
            project_id=data["project_id"],
            private_key_id=data["private_key_id"],
            private_key=data["private_key"],
            client_email=data["client_email"],
            client_id=data["client_id"],
            token_uri=data["token_uri"],
        )

    def to_google_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "type": "service_account",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{self.client_email}",
            }
        )
        return payload


@dataclass
class FirebaseConfig:
    path: Path
    web: WebConfig
    service_account: ServiceAccount

    @classmethod
    def load(cls, path: Path) -> "FirebaseConfig":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        try:
            web_raw = payload["web"]
            svc_raw = payload["serviceAccount"]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError("firebase.json must have 'web' and 'serviceAccount'") from exc

        web = WebConfig.from_dict(web_raw)
        service_account = ServiceAccount.from_dict(svc_raw)
        return cls(path=path, web=web, service_account=service_account)


def find_config(path: Optional[Path] = None) -> Optional[FirebaseConfig]:
    """Return config if present, otherwise ``None``."""

    target = path or (Path.home() / ".biome" / "firebase.json")
    if not target.exists():
        return None
    return FirebaseConfig.load(target)
