# Biome Clipboard Initiative Plan

_Last updated: 2025-12-01_

## 1. Vision & Guiding Principles
- Deliver a seamless clipboard-sharing experience between Windows desktop (tray-first) and Android (Flutter) with room for future iOS expansion.
- Minimize user effort: clipboard capture ➜ tray action ➜ phone notification ➜ single-tap action.
- Favor lightweight, pay-per-use infrastructure and local-first controls where feasible.
- Document major decisions so Android/Desktop teams (and future contributors) can stay aligned.

## 2. Platform Scope
- **Desktop:** Windows-only tray utility for now. Requires revamped config UI for status, recent clip preview, auto-send toggles, and device settings.
- **Mobile:** Net-new Flutter app targeting Android initially. Must expose native capabilities for foreground notification actions and clipboard writes. Keep implementation log (Section 8) updated as desktop-side expectations evolve.
- **Future:** Hooks for iOS client, additional desktops, and multi-device "biome" sync once core pipeline is stable.

## 3. Clipboard Payload Types & UX Contracts
| Payload | Desktop Experience | Android Notification Action | Notes |
| --- | --- | --- | --- |
| Plain text | Prompt or auto-send via tray | "Copy to clipboard" | MVP critical path.
| URLs | Optional confirmation, metadata (title/domain) | "Open in browser" + copy fallback | Add domain safety prompts later.
| Images | Send as downloadable blob (no auto copy) | "Download" / view | Requires storage delivery path.
| Files | Same as images but with filename + size | "Download" | Enforce size limits.
| Rich text | Fall back to text-only initially | Same as plain text | Explore HTML/RTF later.

## 4. Transport & Backend
- **Provider:** Firebase (Auth + Cloud Functions/Firestore + FCM) chosen for generous free tier, push notifications, and mature SDKs.
- **Pattern:** Desktop publishes clip metadata -> raw payload goes into Firebase Storage, metadata (type, Storage path, size, action hints) lands in Firestore. Cloud Function/Firebase Messaging notifies target devices to fetch from Storage.
- **Cost control:** Use on-demand functions, short-lived storage objects, and avoid always-on servers.
- **Desktop transport (current state):** Until Firebase credentials are wired up, the desktop client spools outgoing payloads to `~/.biome/outbox/{uuid}.json`. Once config exists at `~/.biome/firebase.json`, the same class will switch to real HTTPS calls.
- **Runtime flow:**
   1. Build OAuth 2.0 token from the service account (scopes: Storage, Firestore, FCM).
   2. Upload serialized payload JSON to Firebase Storage at `clips/<accountId>/<clipId>.json`.
   3. Create Firestore doc under `accounts/{accountId}/clips/{clipId}` referencing the storage object.
   4. (Coming soon) Trigger FCM so Android learns about the clip.
- **Diagnostics:** `python -m scripts.test_transport` exercises the transport end-to-end with a synthetic text payload and reports storage/doc paths on success.
- **Config file layout (`~/.biome/firebase.json`):**
   ```json
   {
      "web": {
         "apiKey": "…",
         "authDomain": "…",
         "projectId": "…",
         "storageBucket": "…",
         "messagingSenderId": "…",
         "appId": "…"
      },
      "serviceAccount": {
         "project_id": "…",
         "private_key_id": "…",
         "private_key": "-----BEGIN PRIVATE KEY-----…",
         "client_email": "…",
         "client_id": "…",
         "token_uri": "https://oauth2.googleapis.com/token"
      }
   }
   ```
   The `web` block comes from the Firebase Web App config snippet; the `serviceAccount` block is the JSON downloaded from Project Settings ▸ Service accounts. The transport loader validates both sections and can be hot-reloaded without restarting the app.
- **Account/Device overrides:** desktop currently derives `accountId` from the Firebase `projectId`, but you can override it (and the device ID) via `BIOME_ACCOUNT_ID` / `BIOME_DEVICE_ID` environment variables until auth is implemented.
- **Storage path convention:** `clips/<accountId>/<clipId>.json` stores the serialized payload (or references binary blobs later). `clipId` is a ULID/UUID generated on the desktop client.
- **Firestore collections:**
   - `accounts/{accountId}` — minimal profile (email, createdAt, device list).
   - `accounts/{accountId}/clips/{clipId}` — document with fields:
      - `storagePath`: string (`clips/...`)
      - `kind`: `text` | `url` | `image` | `file`
      - `metadata`: map (length, domain, mime, etc.)
      - `senderDeviceId`: string
      - `targetDeviceIds`: array (future multi-device fan-out; default phone only)
      - `createdAt`: server timestamp
      - `status`: `queued` | `delivered` | `failed`
- **Notification flow:** Once Firestore doc is written, a Cloud Function (later) or the desktop app itself triggers FCM with the `clipId`. Android fetches the doc, downloads the Storage blob, and acts on it.

## 5. Authentication & Security
- Email/password accounts with optional 2FA (TOTP/SMS if supported by Firebase). Desktop stays logged in; refresh tokens handled silently.
- Device registration stored per account to support future multi-device biomes.
- **Encryption:** Phase 1 uses TLS + Firebase security rules. Design API to swap in E2E (client-managed keys, payload envelopes) without schema break.

## 6. Desktop Client Workstreams
> Desktop app will be refactored into clear modules (clipboard watcher, payload classifier, transport client, tray/UI shell, settings store) instead of the legacy single-script layout so each service can evolve independently.

Current scaffold lives under `biome_desktop/`:
- `clipboard/watcher.py`
- `payloads/classifier.py`
- `transport/firebase_client.py`
- `ui/tray.py`
- `settings/store.py`
- `app.py` (wires everything together)

1. **Core Services**
   - Clipboard watcher (text + rich payload detection).
   - Payload classifier/normalizer (text/link/image/file).
   - Transport client (Firebase SDK wrapper + retry queue).
2. **Tray & UI**
   - Quick send from tray with configurable confirmation.
   - Status mini-view (last clip, connection state).
   - Full config window: account info, device rules, privacy toggles.
3. **Settings & Rules**
   - Local persistence (JSON/SQLite) for prompts, filters ("never auto-send links"), and feature flags.
   - Hooks to sync or export settings later.

Implementation snapshot:
- Clipboard watcher polls via lightweight `tkinter` reads every ~750 ms (Windows-only) so we can avoid pywin32 until binary payloads are required.
- Settings store persists JSON at `~/.biome/settings.json`; exposes simple auto-send rules for text/URLs.
- Tray controller uses `pystray` + `tkinter` prompts (functional but not yet stylized) so features work before polishing.
- Firebase transport persists envelopes to disk until credentials are provided, ensuring nothing is lost while backend work catches up.
- Config dialog: launched from the tray menu, a Tk window exposes toggles for “auto-send text” and “auto-send URLs”, and offers a shortcut to open the outbox folder for debugging. Account/device info panes will light up once Firebase auth lands. Changes persist immediately to the JSON settings file.

## 7. Android (Flutter) Requirements Snapshot
- Flutter app (Dart) with native platform channels for clipboard + notification actions.
- Firebase Auth + FCM integration, mirroring desktop auth.
- Foreground notification with contextual buttons per payload type (copy/open/download).
- Background fetch of payload (FireStore/Cloud Storage) with integrity checks before writing clipboard or launching intents.
- Minimal UI: login, device list, history placeholder (future), settings for prompts.
- Implementation log maintained in Section 8 during desktop-side development.

## 8. Android Implementation Log (for future work)
| Date | Desktop expectation / decision | Android work implied |
| --- | --- | --- |
| 2025-12-01 | Payload types include text, URLs, images, files with distinct actions. | Implement action-specific notification buttons and handlers (copy, open, download) in Flutter + native plugins. |
| 2025-12-01 | Local device rules (auto-send, link confirmations) stay client-side. | Mirror rule storage locally on Android; no backend sync yet. |
| 2025-12-01 | Firebase chosen for auth/messaging. | Use Firebase Auth/FCM packages for Flutter; set up topic/subscription per device. |

## 9. Milestones & Next Steps
1. **Desktop MVP**
   - Integrate Firebase Auth (login/refresh) and messaging client.
   - Clipboard watcher ➜ payload serializer ➜ push to Firebase.
   - Basic tray flow (prompt/auto-send) + config UI skeleton.
2. **Android MVP**
   - Flutter app with login, device registration, FCM listener, notification actions writing to clipboard or launching intent.
3. **Hardening**
   - Payload validation, rate limiting, optional E2E encryption, history view groundwork, multi-device routing logic.

## 10. Open Questions
- Strategy for revocation/device unlinking from desktop UI.
- Timeline for E2E encryption investment.

---
Keep this document updated whenever we refine architecture, make trade-offs, or add Android expectations.
