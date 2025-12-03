using System.Threading;
using System.Threading.Tasks;
using Biome.Desktop.Core.Dispatch;
using Biome.Desktop.Core.Payloads;
using Biome.Desktop.Core.Transport;
using Biome.Desktop.App.Tray;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Biome.Desktop.App.Dispatch;

public sealed class PayloadDispatchService : BackgroundService
{
    private readonly IPayloadDispatchQueue _queue;
    private readonly IPayloadTransport _transport;
    private readonly ITrayService _trayService;
    private readonly ILogger<PayloadDispatchService> _logger;

    public PayloadDispatchService(
        IPayloadDispatchQueue queue,
        IPayloadTransport transport,
        ITrayService trayService,
        ILogger<PayloadDispatchService> logger)
    {
        _queue = queue;
        _transport = transport;
        _trayService = trayService;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var payload in _queue.ReadAllAsync(stoppingToken))
        {
            try
            {
                _trayService.SetState(TrayIconState.Sending, "Uploading clipboard to Biome…");
                _logger.LogInformation("Dispatching payload {PayloadId} (Type: {PayloadType}).", payload.Id, payload.Kind);
                await _transport.SendAsync(payload, stoppingToken).ConfigureAwait(false);
                _trayService.SetState(TrayIconState.Sent, "Clipboard delivered to Biome.");
                _logger.LogInformation("Payload {PayloadId} sent.", payload.Id);

                // Reset to Idle after a short delay so the user sees the success state briefly
                await Task.Delay(2000, stoppingToken).ConfigureAwait(false);
                _trayService.SetState(TrayIconState.Idle);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                _trayService.SetState(TrayIconState.Error, "Failed to upload clipboard. Check logs.");
                _logger.LogError(ex, "Failed to dispatch payload {PayloadId}.", payload.Id);
            }
        }
        _trayService.SetState(TrayIconState.Idle, "Clipboard service stopped.");
    }
}
