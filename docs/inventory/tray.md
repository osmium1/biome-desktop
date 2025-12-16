# Tray Integration

Biome Desktop currently relies on a temporary `NotifyIcon` implementation until the WinUI tray/command surface is rebuilt. This doc shows how `TrayService` wires menu commands into clipboard capture and window toggling.

## Lifecycle
`TrayLifecycleService` runs as an `IHostedService` and simply delegates to `ITrayService`:

```csharp
public async Task StartAsync(CancellationToken cancellationToken)
{
    _logger.LogInformation("Starting tray lifecycle service.");
    await _trayService.InitializeAsync(cancellationToken).ConfigureAwait(false);
    _trayService.SetState(TrayIconState.Idle, "Biome Desktop ready");
}
```

This ensures the icon appears as soon as the host starts and that it transitions back to "shutting down" on stop.

## `TrayService` core
`TrayService` itself lives in `src/Biome.Desktop.App/Tray/TrayService.cs` and is registered as a singleton. It depends on:
- `IClipboardService` to capture data on demand.
- `IPayloadDispatchQueue` to push payloads into background processing.
- `IMainWindowController` to show/hide the console window or settings surface.

```csharp
public async Task InitializeAsync(CancellationToken cancellationToken)
{
    using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken, _cts.Token);
    await _dispatcher.InvokeAsync(() =>
    {
        _menu = BuildContextMenu();
        _notifyIcon = new NotifyIcon
        {
            Icon = ResolveIcon(TrayIconState.Idle),
            Visible = true,
            Text = "Biome Desktop (Idle)",
            ContextMenuStrip = _menu
        };
        _notifyIcon.MouseClick += OnNotifyIconMouseClick;
    }, DispatcherPriority.Normal, linkedCts.Token).Task.ConfigureAwait(false);
}
```

The dispatcher hop is required because Windows Forms components expect STA threads.

### Context menu commands
`BuildContextMenu` constructs five entries:
1. `Open/Hide Biome console` → toggles the main WPF window.
2. `Settings` → `IMainWindowController.ShowSettings()` (spawns a `SettingsWindow`).
3. Separator.
4. `Send clipboard` → calls `HandleSendClipboardAsync` (same as left-click shortcut).
5. Separator.
6. `Exit Biome` → shuts down the WPF application.

```csharp
private async Task HandleSendClipboardAsync()
{
    try
    {
        SetState(TrayIconState.Sending);
        var payload = await _clipboardService.CaptureAsync(_cts.Token).ConfigureAwait(true);
        if (payload is null)
        {
            SetState(TrayIconState.Idle);
            MessageBox.Show("Clipboard is empty or contains unsupported content.", ...);
            return;
        }

        await _dispatchQueue.EnqueueAsync(payload, _cts.Token).ConfigureAwait(true);
        SetState(TrayIconState.Waiting);
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Tray send clipboard command failed.");
        SetState(TrayIconState.Error);
        MessageBox.Show($"Send failed: {ex.Message}", ...);
    }
}
```

### Icon assets
Because no embedded ICOs exist yet, the service dynamically draws tiny colored icons at runtime using `System.Drawing`. Each `TrayIconState` maps to a color/glyph combination:

- `Idle` → blue circle with `B`.
- `Waiting` → orange ellipsis.
- `Sending` → purple arrow.
- `Sent` → green check.
- `Error` → red exclamation.

These icons are cached in `_stateIcons` and disposed when the tray shuts down.

### Idle / legacy remnants
- Balloon tip support is stubbed out (comment notes they are only desirable for errors, but currently no call to `ShowBalloonTip`).
- `_trayService.SetState(TrayIconState.Error, tooltip)` is the only place that would display textual feedback; success relies purely on icon transitions.
- When WinUI tray controls replace `NotifyIcon`, the dispatcher-bound drawing logic can be removed.
