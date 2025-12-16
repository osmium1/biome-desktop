# Configuration + Settings Binding

## `BiomeSettings`
`Biome.Desktop.Core/Configuration/BiomeSettings.cs` provides strongly-typed access to the `Biome` section.

```csharp
public sealed class BiomeSettings
{
    public FirebaseSettings Firebase { get; init; } = new();
    public ClipboardSettings Clipboard { get; init; } = new();

    public sealed class FirebaseSettings
    {
        public string ProjectId { get; init; } = string.Empty;
        public string ServiceAccountPath { get; init; } = string.Empty;
        public string DeviceToken { get; init; } = string.Empty;
        public string StorageBucket { get; init; } = string.Empty;
    }

    public sealed class ClipboardSettings
    {
        public bool AutoQueueFromWatcher { get; init; } = false;
    }
}
```

`App.BuildHost` calls `builder.Services.Configure<BiomeSettings>(builder.Configuration.GetSection("Biome"));`. As a result, any component can depend on `IOptions<BiomeSettings>` (or `IOptionsMonitor<>` if hot reload is needed) to access Firebase credential paths or clipboard behavior flags.

## `appsettings.json`
The root file is intentionally sparse so the repo can ship without secrets:

```json
{
  "Biome": {
    "Firebase": {
      "ProjectId": "",
      "ServiceAccountPath": "",
      "DeviceToken": "",
      "StorageBucket": ""
    }
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft": "Warning",
      "Microsoft.Hosting.Lifetime": "Information"
    }
  }
}
```

`appsettings.Development.json` overrides only logging (sets Default to `Debug`). When running locally, developers should either:
1. Edit `appsettings.Development.json` with their Firebase values (not recommended for committed changes), or
2. Provide environment variables prefixed with `BIOME__`, e.g. `BIOME__Firebase__ServiceAccountPath=C:\Users\you\.biome\firebase.json`.

## Access patterns
- `FirebasePayloadTransport` uses `IOptions<BiomeSettings>` to locate service account JSON and optional device token.
- `ClipboardWatcherService` checks `settings.Value.Clipboard.AutoQueueFromWatcher` but—as noted in `status.md`—never acts on it.
- `SettingsWindow` reads the same options to pre-fill the UI and offers a file picker, but it does not persist modifications.

## Improvement ideas
1. Adopt `IOptionsMonitor<BiomeSettings>` for services that need to react to overwritten `appsettings.json` without restarting the host.
2. Introduce a `userconfig.json` under `%APPDATA%/Biome` that the Settings UI can edit safely. This file can be layered onto the host configuration via another `.AddJsonFile` call before `AddEnvironmentVariables`.
3. Provide validation (perhaps via `IValidateOptions<BiomeSettings>`) so misconfigured Firebase entries fail fast during startup rather than at first send attempt.
