# Current Work & Scratchpad

**Status:** Rework Phase 0 → Phase 1 Kickoff
**Last Updated:** Dec 3, 2025 (Image Support Added)

---

## 🔴 Immediate Action Items

1.  **Host + configuration scaffold ✅**
    *   `Biome.Desktop.sln` (WPF + Core) targets .NET 10, loads `appsettings*.json`, and maps `BIOME__` env vars into `BiomeSettings`.
    *   Logging pipeline wired via `Microsoft.Extensions.Logging` (Debug + Console providers).

2.  **Tray + background services ✅**
    *   Temporary Windows Forms `NotifyIcon` mirrors the legacy tray: commands for opening/closing the console window, sending clipboard, and exiting the app.
    *   `MainWindow` no longer quits the process—closing hides it so the tray stays resident, matching the Tk flow.
    *   DI continues to wire `MainWindow`, `IMainWindowController`, tray services, clipboard service, dispatch queue, and transport service.

3.  **Clipboard watcher & queue ✅**
    *   `ClipboardWatcherService` listens for clipboard changes and updates the tray state. Automatic enqueueing is now opt-in via `Biome:Clipboard:AutoQueueFromWatcher` (defaults to manual send).
    *   `PayloadDispatchService` drains the queue (from manual sends for now) and invokes the Firebase transport; the dev button still enqueues rather than sending inline.
    *   **Update:** `ClipboardService` now captures images (PNG bytes) in addition to text.

4.  **Firebase config + token provider ✅**
    *   Added strongly-typed `firebase.json` loader (web + serviceAccount) plus validation helpers in `Biome.Desktop.Core`.
    *   `FirebaseTokenProvider` now signs JWTs with the service account private key, exchanges them for OAuth tokens (Storage/Firestore/FCM), and caches tokens until one minute before expiry.

5.  **Firebase transport pipeline 🚧**
    *   `FirebasePayloadTransport` consumes the config + token provider, uploads text and image payloads to Cloud Storage, writes Firestore docs, and optionally sends FCM notifications (when `DeviceToken` is provided).
    *   Images are uploaded as Base64-encoded data within the JSON envelope (Kind: "image").
    *   Every failure path still writes an envelope to `%USERPROFILE%/.biome/outbox/{guid}.json` with context such as `firebase-config-invalid`, `firebase-token-unavailable`, or `firebase-send-error`.
    *   Next: add retries/metrics, and surface transport telemetry in the diagnostics panel.

6.  **Diagnostics & notifications**
    *   Start experimenting with Windows App SDK App Notifications for send success/failure toasts.
    *   Add temporary log viewer surface in `MainWindow` for early troubleshooting until the tray UI is complete.

---

## 🗂 Phase 1 Task Breakdown

1.  **Shell & Hosting**
    *   Create `Biome.Desktop.App` WPF project with DI bootstrapper and placeholder window.
    *   Wire `Microsoft.Extensions.Hosting` + `IHostedService` scaffolding to match the legacy app lifecycle.

2.  **Tray & Commands**
    *   Implement tray service abstraction plus initial command set (Send Clipboard, Share Image, Quit).
    *   Introduce state machine for icon swaps (Idle/Waiting/Sending/Sent) modeled after Python enum.

3.  **Clipboard & Payload Buffer**
    *   Port clipboard watcher with throttling + format detection.
    *   Serialize payload metadata using `BiomeSettings` defaults and queue to transport service.
    *   ✅ Interfaces (`IClipboardService`, `IPayloadTransport`) now stubbed with placeholder implementations for future wiring.

4.  **Transport Layer**
    *   Implement Firebase REST client (Storage upload, Firestore metadata write, FCM data-only send).
    *   Instrument with structured logging + retries; expose diagnostics pane hook.

5.  **Notifications & Logging**
    *   Integrate Windows App SDK notifications for immediate feedback.
    *   Map `BIOME_LOG_LEVEL` ➜ `ILogger` categories and add log viewer window.

6.  **Configuration & Secrets**
    *   Finalize `appsettings` schema, secure secret storage, and onboarding experience.
    *   Document developer setup steps in `docs/CONFIGURATION.md`.

---

## 🔄 Feature Track Order (Next Iterations)

1.  **Clipboard Watcher & Queue** – finalize throttled watcher, support text/images, and expose a background queue that the tray commands can drain.
2.  **Tray Menu & Icon States** – bind the watcher/send commands into the Windows App SDK tray, reflecting legacy icon states (Idle/Waiting/Sending/Sent/Error).
3.  **Firebase Transport** – replace the stub with Storage upload + Firestore metadata + FCM send, including retries and diagnostics events.
4.  **Notifications & Diagnostics** – surface App Notifications for success/failure, embed a log viewer for troubleshooting, and emit telemetry hooks.
5.  **Packaging & Secrets UX** – integrate Credential Locker/onboarding flow for service accounts, prep MSIX project, and validate startup behaviors.

---

## 📎 Reference Points
*   **Legacy Location:** `legacy/python-desktop/biome_desktop/...`
*   **Firebase Contract:** Storage path `payloads/{clip_id}`, Firestore document `payloads/{clip_id}` with fields `{ type, size, checksum, download_url, created_at }`.
*   **FCM Endpoint:** `https://fcm.googleapis.com/v1/projects/{project_id}/messages:send` (Bearer scope `https://www.googleapis.com/auth/firebase.messaging`).
*   **Platform Baseline:** .NET 10.0 + Windows App SDK 1.8.3 (runtime/package build 1.8.251106002) validated as fully supported on Windows 11.

---

## 📝 Notes
*   Preserve BIOME_LOG_LEVEL semantics by mapping to `Logging:LogLevel:Default` when configuring `ILoggerFactory`.
*   Tray UX goal: <150 ms feedback between click and toast/icon change, even while upload continues in background.
*   Consider hosting transport logic in a worker service class library so a future CLI agent can reuse it.
