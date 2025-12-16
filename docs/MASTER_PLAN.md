# Biome: Master Project Plan

**Vision:** Deliver a trustworthy cross-device clipboard bridge whose Windows experience feels native, modern, and instantaneous. Biome favors explicit sends and meaningful notifications over silent syncing so users always stay in control.

---

## 1. Strategic Direction

1.  **Windows-first rework:** Rebuild the desktop client with .NET 10 LTS + WPF/WinUI 3 (Windows App SDK 1.8.3) for a polished, high-performance tray/notification experience.
2.  **Legacy preserved:** The full Python implementation now lives under `legacy/python-desktop` for reference while we replicate functionality feature-by-feature.
3.  **Incremental parity:** Each .NET phase closes the gap with the Python behavior before layering new UX and security capabilities.
4.  **Mobile & cloud continuity:** The Flutter receiver and Firebase backend remain in scope; new desktop code must integrate with the existing Firestore/Storage/FCM schema.

---

## 2. User Workflows (Target State)

### A. Desktop ➜ Phone (Text & URLs)
1.  User copies text on Windows (`Ctrl+C`).
2.  Tray menu shows **Send Clipboard** with live preview.
3.  Click triggers background upload + progress toast.
4.  Phone receives FCM notification and exposes "Copy" action.

### B. Desktop ➜ Phone (Images & Files)
1.  Tray menu exposes **Share Image/File…** picker.
2.  Transfer pipeline streams to Firebase Storage with progress indicator.
3.  Phone notification provides "Download" deep link.

### C. Phone ➜ Desktop (Later Phase)
1.  Android app sends payload via existing Firebase contracts.
2.  Windows app listens for new documents and surfaces a toast with "Copy" / "Save As".

---

## 3. Architecture & Tech Stack

### Windows Desktop (New)
*   **Runtime:** .NET 10.0 LTS (SDK 10.0.100)
*   **UI Framework:** WPF hosting WinUI 3 controls via Windows App SDK 1.8.3 (stable channel) for modern styles + tray interop.
*   **Project Style:** SDK-style solution with multi-targetable class libraries for transport, telemetry, and domain logic.
*   **Key Libraries:** CommunityToolkit.Mvvm (MVVM), Windows App SDK (1.8.251106002), System.Text.Json, Firebase Admin REST via `HttpClient`.
*   **Tooling Requirements:** Visual Studio 2022 17.1+ (or VS 2026 preview for built-in .NET 10) with Windows 11 SDK 19041+ and Windows App SDK VSIX from Marketplace.
*   **Packaging:** MSIX (stretch goal) with auto-start toggle.

### Windows Desktop (Legacy)
*   **Location:** `legacy/python-desktop`
*   **Purpose:** Reference implementation for Firebase contract, notification copy, and tray behavior.

### Mobile (Separate Repo)
*   Flutter (Android first) remains the receiver/emitter of payloads.

### Cloud (Shared)
*   Firebase Storage/Firestore/FCM contracts stay unchanged to minimize backend churn during the rework.

---

## 4. Development Phases (Rework Roadmap)

### Phase 0 – Legacy Freeze ✅
*   Archive Python desktop under `legacy/python-desktop`.
*   Snapshot Firebase contract + config expectations.

### Phase 1 – WPF Core Shell
*   Initialize `Biome.Desktop.sln` with WPF app + core class library targeting `net10.0-windows10.0.19041.0` and `net10.0` respectively.
*   Implement dependency injection, configuration (JSON + secrets), and structured logging via the generic host (✅ complete).
*   Stub tray icon service + placeholder commands that log state transitions (✅ complete).
*   Introduce typed seams for clipboard capture + payload transport (`IClipboardService`, `IPayloadTransport`, `ClipboardPayload`) to unblock Phase 2 work (✅ complete).

### Phase 2 – Clipboard & Transport Layer
*   Port clipboard watcher/buffer using Windows Clipboard APIs.
*   Implement Firebase transport (Storage + Firestore + FCM) via HttpClient with exponential retry.
*   Establish background dispatch queue mirroring Python async send semantics.

### Phase 3 – UX & Notification Polish
*   Replace placeholder tray commands with full send flow (stateful icon, command availability, progress toast).
*   Integrate Windows notifications (WinUI AppNotification / Toast).
*   Expose logging/diagnostics panel for troubleshooting.

### Phase 4 – Phone ➜ Desktop & Attachments
*   Add listener for Firebase change stream (Firestore listening or polling).
*   Surface phone-originated payloads with actionable toasts (copy/download).
*   Harden binary/image support and introduce payload size guards + previews.

### Phase 5 – Hardening & Extras
*   End-to-end encryption design + rollout.
*   MSIX distribution, auto-update hooks, and telemetry opt-in.
*   Performance tuning, accessibility, and localization groundwork.

---

## 5. Project Structure Strategy
*   **Root:** Hosts the new .NET solution, docs, and infrastructure assets.
*   **`legacy/python-desktop`:** Frozen Python client, scripts, and requirements for reference/testing.
*   **`docs/`:** Living documentation (this plan + `CURRENT_WORK.md`).
*   **`mobile/` (future):** Flutter receiver once active development resumes.

---

## 6. Success Criteria
1.  Windows client reaches feature parity with the Python tray flow (clipboard send, image upload, FCM notify).
2.  UX latency < 300 ms from tray click to visible acknowledgement.
3.  Recoverable failures (network/offline) with actionable toasts + diagnostics.
4.  Codebase prepared for future cross-platform investment (clear separations between UI, domain, and Firebase transport).
