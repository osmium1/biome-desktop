# Idle / Legacy Code Scan

The goal of this pass was to identify code paths that no longer run or that still reference the Python-era behavior. Items below should be reviewed before release.

| Area | File | Observation | Suggested action |
| --- | --- | --- | --- |
| Clipboard watcher | `ClipboardWatcherService` | Service immediately sleeps forever; `ShouldEnqueue` helper is unused. | Remove hosted service registration until auto-send returns, or implement the polling loop guarded by `BiomeSettings.Clipboard.AutoQueueFromWatcher`. |
| Settings persistence | `Windowing/SettingsWindow.xaml.cs` | Save button only shows a message box. Device ID and Firebase path edits never hit disk or override configuration. | Introduce a writable user settings file (e.g., `%APPDATA%/Biome/appsettings.user.json`) and reload the bound `BiomeSettings`. |
| Dashboard feedback | `Pages/DashboardPage.xaml.cs` | Bypasses tray state machine, so sending from the dashboard never updates icon/tooltips. | Inject a shared status/notification service or publish events so tray UI reflects actions triggered outside the tray. |
| Clipboard payload kinds | `ClipboardPayloadKind.File` | Enum contains `File` but no producer creates file payloads; transport logic also lacks file handling. | Remove the enum value or implement drag/drop/file clipboard capture plus transport serialization. |
| Firebase config cache | `FirebasePayloadTransport` | `_cachedConfig` never invalidates when `appsettings.json` reloads; host reload-on-change won't refresh the already-built singleton. | Listen for `IOptionsMonitor<BiomeSettings>` change notifications or expose a manual cache reset when service account path changes. |
| Outbox retention | `.biome/outbox` | Files accumulate indefinitely; no pruning job exists. | Add a maintenance background task or expose a command to purge old envelopes. |
