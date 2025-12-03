# Desktop Configuration Plan

This document captures how the new .NET 10 client (paired with Windows App SDK 1.8.3) will load secrets, Firebase settings, and runtime toggles while remaining faithful to the legacy Python behavior.

## 1. Files & Secrets

| Source | Legacy (Python) | .NET Replacement | Notes |
| --- | --- | --- | --- |
| Firebase service account | `~/.biome/firebase.json` | Same combined `firebase.json` file read from `BiomeSettings:Firebase:ServiceAccountPath` | Defaults to `%USERPROFILE%\.biome\firebase.json`; must include both `web` + `serviceAccount` blocks. |
| Device token | `BIOME_FCM_DEVICE_TOKEN` env var | `BiomeSettings:Firebase:DeviceToken` in `appsettings.Development.json` or encrypted secret provider | Never checked into git. |
| Log level | `BIOME_LOG_LEVEL` env var | `Logging:LogLevel:Default` (maps to `Microsoft.Extensions.Logging`) | Accepts `Trace`, `Debug`, etc. |
| Windows App SDK runtime | Implicit via Python deps | Windows App SDK 1.8.3 runtime installer (matching NuGet version 1.8.251106002) | Required for unpackaged deployment. |
| Clipboard watcher behavior | Local logic | `BiomeSettings:Clipboard:AutoQueueFromWatcher` (bool, default `false`) | When `false`, clipboard changes only update tray state; sending occurs when the user clicks Send. |

## 2. Configuration Sources

1. `appsettings.json` (checked in, safe defaults only).
2. `appsettings.Development.json` (gitignored, developer overrides).
3. Environment variables prefixed with `BIOME__` for quick overrides (e.g., `BIOME__Firebase__ServiceAccountPath`).
4. Secrets stored via Windows Credential Locker for high-sensitivity values; the WPF app will provide a one-time onboarding dialog to capture them.
5. Optional runtime overrides for identity/notifications via `BIOME_ACCOUNT_ID`, `BIOME_DEVICE_ID`, and `BIOME_FCM_DEVICE_TOKEN` (mirrors the Python client).

## 3. Binding Model

Settings are bound into `BiomeSettings` (see `Biome.Desktop.Core/Configuration/BiomeSettings.cs`). Consumers request strongly-typed options via `IOptions<BiomeSettings>`; the Firebase transport now loads/parses the legacy `firebase.json`, validates required fields, and surfaces actionable errors through the diagnostics panel.

### 3.1 Firebase JSON layout

Place the combined config file at `%USERPROFILE%\.biome\firebase.json` and point `BiomeSettings:Firebase:ServiceAccountPath` to it (or override via `BIOME__Firebase__ServiceAccountPath`). The loader expects:

```json
{
	"web": {
		"apiKey": "...",
		"authDomain": "...",
		"projectId": "your-project",
		"storageBucket": "your-project.appspot.com",
		"messagingSenderId": "...",
		"appId": "..."
	},
	"serviceAccount": {
		"project_id": "your-project",
		"private_key_id": "...",
		"private_key": "-----BEGIN PRIVATE KEY-----\n...",
		"client_email": "firebase-adminsdk@your-project.iam.gserviceaccount.com",
		"client_id": "...",
		"token_uri": "https://oauth2.googleapis.com/token"
	}
}
```

Validation errors (missing bucket, malformed private key, etc.) are recorded in the outbox (`%USERPROFILE%\.biome\outbox`) with reasons like `firebase-config-invalid` so they can be inspected without running the UI.

### 3.2 Token minting & transport

`FirebaseTokenProvider` signs JWTs with the service account private key, exchanges them for OAuth tokens (scopes: Storage, Firestore, FCM), and caches them until one minute before expiry. `FirebasePayloadTransport` then:

1. Uploads serialized payloads to Cloud Storage (`clips/{accountId}/{clipId}.json`).
2. Creates Firestore documents under `accounts/{accountId}/clips/{clipId}`.
3. Sends optional FCM notifications when `DeviceToken` or `BIOME_FCM_DEVICE_TOKEN` is provided.

Any failure along the way still writes an outbox envelope with diagnostic context so no clipboard data is lost.

## 4. Tooling & Runtime Prereqs (Dec 2025)

| Component | Minimum | Recommended |
| --- | --- | --- |
| .NET SDK | 8.0 | **10.0.100 (LTS)** |
| Visual Studio | 2022 17.1 | 17.14+ (or VS 2026 preview with built-in .NET 10) |
| Windows SDK | 2004 / build 19041 | Latest available via VS installer |
| Windows App SDK NuGet | 1.8.251106002 | Same |
| Windows App SDK Runtime | 1.8.251106002 | Same |
| OS | Windows 10 1809+ | Windows 11 23H2+ |

## 5. Migration Checklist

- [ ] Create `appsettings.json` skeleton with `Firebase` defaults (device token placeholder, service-account path hint) plus logging settings.
- [ ] Ship an onboarding command that imports an existing `firebase.json` file into the secure location.
- [ ] Implement `ISecretStore` abstraction backed by Credential Locker for tokens and future encryption keys.
- [ ] Provide CLI utility (future) to test credentials without launching the WPF shell.
