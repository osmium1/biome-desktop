# Payload Dispatch Pipeline

This document traces how clipboard captures move from the UI into the background transport via `IPayloadDispatchQueue` and `PayloadDispatchService`.

## Queue implementation
The queue is a thin wrapper over `System.Threading.Channels` that allows multiple producers (tray command + dashboard page) and a single consumer (`PayloadDispatchService`).

```csharp
// src/Biome.Desktop.App/Dispatch/PayloadDispatchQueue.cs
public sealed class PayloadDispatchQueue : IPayloadDispatchQueue
{
    private readonly Channel<ClipboardPayload> _channel;

    public PayloadDispatchQueue()
    {
        var options = new UnboundedChannelOptions
        {
            AllowSynchronousContinuations = false,
            SingleReader = false,
            SingleWriter = false
        };
        _channel = Channel.CreateUnbounded<ClipboardPayload>(options);
    }

    public ValueTask EnqueueAsync(ClipboardPayload payload, CancellationToken cancellationToken)
        => _channel.Writer.WriteAsync(payload, cancellationToken);

    public IAsyncEnumerable<ClipboardPayload> ReadAllAsync(CancellationToken cancellationToken)
        => _channel.Reader.ReadAllAsync(cancellationToken);
}
```

The contract lives in `Biome.Desktop.Core.Dispatch.IPayloadDispatchQueue`, keeping app vs. core separation clean.

## Background dispatcher
`PayloadDispatchService` is a hosted service that blocks on `ReadAllAsync`, pushing each payload through the configured transport and updating the tray icon for user feedback.

```csharp
// src/Biome.Desktop.App/Dispatch/PayloadDispatchService.cs
protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    await foreach (var payload in _queue.ReadAllAsync(stoppingToken))
    {
        try
        {
            _trayService.SetState(TrayIconState.Sending, "Uploading clipboard to Biome…");
            await _transport.SendAsync(payload, stoppingToken).ConfigureAwait(false);
            _trayService.SetState(TrayIconState.Sent, "Clipboard delivered to Biome.");

            await Task.Delay(2000, stoppingToken).ConfigureAwait(false);
            _trayService.SetState(TrayIconState.Idle);
        }
        catch (Exception ex)
        {
            _trayService.SetState(TrayIconState.Error, "Failed to upload clipboard. Check logs.");
            _logger.LogError(ex, "Failed to dispatch payload {PayloadId}.", payload.Id);
        }
    }

    _trayService.SetState(TrayIconState.Idle, "Clipboard service stopped.");
}
```

Observations:
- Success path pauses for two seconds so the user visually sees the "Sent" glyph before reverting to Idle.
- Errors both log and surface through the tray icon (no toast from the dispatcher itself; tray may show message boxes in other flows).
- Cancellation via `stoppingToken` gracefully exits and sets the tray text to "Clipboard service stopped."

## Entry points into the queue
- `TrayService.HandleSendClipboardAsync` → `await _dispatchQueue.EnqueueAsync(payload, _cts.Token)`.
- `DashboardPage.OnSendClicked` resolves `IPayloadDispatchQueue` from `App.Services` and enqueues with `CancellationToken.None`.
- The `ClipboardWatcherService` does **not** currently enqueue anything because it idles.

Potential future adjustments:
- Introduce back-pressure limits (bounded channel) once transports are live to avoid unbounded RAM growth.
- Feed dispatch results back into UI via eventing or state store instead of hard-coded two-second sleeps.
