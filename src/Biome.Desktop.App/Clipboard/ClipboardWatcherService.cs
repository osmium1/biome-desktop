using System;
using System.Threading;
using System.Threading.Tasks;
using Biome.Desktop.Core.Clipboard;
using Biome.Desktop.Core.Configuration;
using Biome.Desktop.Core.Dispatch;
using Biome.Desktop.App.Tray;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Biome.Desktop.App.Clipboard;

public sealed class ClipboardWatcherService : BackgroundService
{
    private static readonly TimeSpan PollInterval = TimeSpan.FromSeconds(1);

    private readonly IClipboardService _clipboardService;
    private readonly IPayloadDispatchQueue _dispatchQueue;
    private readonly ILogger<ClipboardWatcherService> _logger;
    private readonly ITrayService _trayService;
    private readonly bool _autoQueueFromWatcher;

    private string? _lastSignature;

    public ClipboardWatcherService(
        IClipboardService clipboardService,
        IPayloadDispatchQueue dispatchQueue,
        ITrayService trayService,
        IOptions<BiomeSettings> settings,
        ILogger<ClipboardWatcherService> logger)
    {
        _clipboardService = clipboardService;
        _dispatchQueue = dispatchQueue;
        _trayService = trayService;
        _logger = logger;
        _autoQueueFromWatcher = settings.Value.Clipboard.AutoQueueFromWatcher;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Clipboard watcher started (Passive Mode).");
        
        // In the new manual-only flow, we don't poll the clipboard.
        // The TrayService explicitly calls CaptureAsync when the user clicks Send.
        // We keep the service running just in case we want to re-enable auto-watch later,
        // but for now it just sleeps.
        
        await Task.Delay(Timeout.Infinite, stoppingToken);
    }

    private bool ShouldEnqueue(Core.Payloads.ClipboardPayload payload)
    {
        if (string.IsNullOrEmpty(payload.TextContent))
        {
            return false;
        }

        var signature = payload.TextContent;
        if (string.Equals(_lastSignature, signature, StringComparison.Ordinal))
        {
            return false;
        }

        _lastSignature = signature;
        return true;
    }
}
