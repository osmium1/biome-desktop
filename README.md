# Biome

Cross-device clipboard sharing platform, migrated from a native Windows (.NET/WPF) stack to Python for faster iteration.

Desktop client (PySide6) sends clipboard content through a FastAPI
backend that persists to Firebase (Cloud Storage + Firestore) and pushes
FCM notifications to linked devices.

## Repo layout

```
api/                    # httpx async client for the backend
clipboard/              # QClipboard watcher
payloads/               # Clipboard classifier
settings/               # JSON persistence (~/.biome/)
tray/                   # QSystemTrayIcon service
ui/                     # Main window, sidebar, pages, overlay, theme
app.py                  # Composition root — wires all services
main.py                 # Entry point: python main.py
schemas/                # Payload JSON schemas
```

## Quick start

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.11+ and a running backend (or it operates offline with
local outbox spooling).

## Architecture

```
┌──────────────┐    POST /api/clips    ┌──────────────┐
│  Desktop App │ ───────────────────►  │  FastAPI      │
│  (PySide6)   │                       │  Backend      │
└──────────────┘                       └──────┬───────┘
                                              │
                               ┌──────────────┼──────────────┐
                               ▼              ▼              ▼
                        Cloud Storage    Firestore     FCM Push
                        (payload blob)   (clip doc)    (notify)
```

## Features

| Feature              | Status  |
|----------------------|---------|
| Dark "Forest Floor" theme | ✅ |
| Custom sidebar nav   | ✅      |
| Dashboard console    | ✅      |
| Settings page        | ✅      |
| System tray (5 states) | ✅   |
| Clipboard watcher    | ✅      |
| SpeedBoost overlay   | ✅      |
| Backend health check | ✅      |
| Clip ingest API      | ✅      |
| Firebase transport   | ✅      |
| Outbox fallback      | ✅      |
| Auto-send rules      | ✅      |

## Tech stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Desktop  | Python 3.12, PySide6, qasync, httpx |
| Backend  | FastAPI, Uvicorn, Pydantic        |
| Infra    | GCP Cloud Run, Cloud Storage, Firestore, FCM |
| IaC      | Terraform (planned)               |
| CI/CD    | GitHub Actions (planned)          |
