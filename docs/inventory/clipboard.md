# Clipboard Capture Layer

This file covers `IClipboardService` and the optional watcher that used to poll the clipboard automatically.

## `ClipboardService`
Located at `src/Biome.Desktop.App/Clipboard/ClipboardService.cs`, this class is registered as the concrete implementation for the shared `IClipboardService` contract. It marshals access back onto the WPF dispatcher so Win32 clipboard APIs are invoked on the UI thread.

```csharp
public sealed class ClipboardService : IClipboardService
{
    private readonly ILogger<ClipboardService> _logger;
    private readonly Dispatcher _dispatcher;

    public ClipboardService(ILogger<ClipboardService> logger)
    {
        _logger = logger;
        _dispatcher = System.Windows.Application.Current?.Dispatcher ?? Dispatcher.CurrentDispatcher;
    }

    public async Task<ClipboardPayload?> CaptureAsync(CancellationToken cancellationToken)
    {
        return await _dispatcher.InvokeAsync(() =>
        {
            if (System.Windows.Clipboard.ContainsImage())
            {
                // Encodes to PNG bytes and wraps with ClipboardPayloadKind.Image
            }

            if (System.Windows.Clipboard.ContainsText())
            {
                // Wraps Unicode text into ClipboardPayloadKind.Text
            }

            _logger.LogWarning("Clipboard does not contain supported content (Text or Image).");
            return null;
        }, DispatcherPriority.Send, cancellationToken);
    }
}
```

Notes:
- Images are always encoded as PNG via `PngBitmapEncoder` before being injected into the payload.
- Text captures use Unicode format and drop empty/whitespace-only content.
- `ClipboardPayload` (in `Biome.Desktop.Core`) carries either `TextContent` or `ImageBytes`. `ClipboardPayloadKind.File` exists but is not generated anywhere yet.

## `ClipboardWatcherService`
This background service remains registered but intentionally idles. It represents the old "auto send" loop from the Python tray which used to poll every second. Today it simply sleeps because the new UX requires manual sends via the tray or dashboard button.

```csharp
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    _logger.LogInformation("Clipboard watcher started (Passive Mode).");

    // In the new manual-only flow, we don't poll the clipboard.
    await Task.Delay(Timeout.Infinite, stoppingToken);
}
```

### Idle / future work
- `ShouldEnqueue` deduplication helper is unused because the watcher never invokes it. If auto-queue returns, `ShouldEnqueue` should be called before `IPayloadDispatchQueue.EnqueueAsync`.
- `BiomeSettings.Clipboard.AutoQueueFromWatcher` is read during construction but never acted upon; the entire watcher body would need to recheck that flag to decide whether to poll.
