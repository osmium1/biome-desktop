# Biome Desktop – Architecture Overview

This document summarizes how the .NET host, dependency injection graph, and top-level windows bootstrapping currently work. It is intended as the entry point for the full inventory.

## Host + configuration pipeline
The WPF `App` class opts into the generic host (`Microsoft.Extensions.Hosting`) so that every service can be registered through DI, logging, and configuration providers:

```csharp
// src/Biome.Desktop.App/App.xaml.cs
public App()
{
    ShutdownMode = ShutdownMode.OnExplicitShutdown;
    _host = BuildHost();
}

private static IHost BuildHost()
{
    var builder = Host.CreateApplicationBuilder();

    builder.Configuration
        .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile($"appsettings.{builder.Environment.EnvironmentName}.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables(prefix: "BIOME__");

    builder.Services.AddHttpClient();
    builder.Services.Configure<BiomeSettings>(builder.Configuration.GetSection("Biome"));

    // Windows + services
    builder.Services.AddSingleton<MainWindow>();
    builder.Services.AddTransient<SettingsWindow>();
    builder.Services.AddSingleton<ITrayService, TrayService>();
    builder.Services.AddSingleton<IFirebaseTokenProvider, FirebaseTokenProvider>();
    builder.Services.AddSingleton<IMainWindowController, MainWindowController>();
    builder.Services.AddSingleton<IClipboardService, ClipboardService>();
    builder.Services.AddSingleton<IPayloadDispatchQueue, PayloadDispatchQueue>();
    builder.Services.AddSingleton<IPayloadTransport, FirebasePayloadTransport>();

    // Hosted background processes
    builder.Services.AddHostedService<TrayLifecycleService>();
    builder.Services.AddHostedService<PayloadDispatchService>();
    builder.Services.AddHostedService<ClipboardWatcherService>();

    builder.Logging.ClearProviders();
    builder.Logging.AddDebug();
    builder.Logging.AddConsole();

    return builder.Build();
}
```

Key observations:
- `appsettings.json` supplies defaults for `Biome.Firebase.*`; environment overrides prefixed with `BIOME__` take priority, which keeps secrets outside source control.
- `MainWindow` is constructed once and hidden by default; `SettingsWindow` is transient so each invocation gets a clean instance.
- Background services (tray lifecycle, dispatch queue, clipboard watcher) start with the host and run until `App.OnExit` stops the host.

## Window bootstrap flow
`OnStartup` wires the DI-managed window controller with the actual `MainWindow` instance, ensuring the hidden-by-default console is controllable from tray commands:

```csharp
protected override async void OnStartup(StartupEventArgs e)
{
    await _host.StartAsync();
    var window = _host.Services.GetRequiredService<MainWindow>();
    MainWindow = window;

    var windowController = _host.Services.GetRequiredService<IMainWindowController>();
    windowController.Initialize(window);
    base.OnStartup(e);
}
```

`MainWindow` itself is built with `Wpf.Ui` controls (`FluentWindow`, `NavigationView`, `TitleBar`) and only exposes the internal dashboard + future history page.

## Cross-project contracts
`Biome.Desktop.Core` houses all interfaces and records shared between UI and background services:

- `IClipboardService`, `ClipboardPayload` – capture contract + payload shape.
- `IPayloadDispatchQueue`, `IPayloadTransport` – queue and transport abstractions.
- `IFirebaseTokenProvider`, `FirebaseConfig` – auth + config parsing.
- `BiomeSettings` – strongly-typed binding for `appsettings.json`.

The app project implements those interfaces so the UI layer can remain thin while business logic migrates over from the legacy Python client.
