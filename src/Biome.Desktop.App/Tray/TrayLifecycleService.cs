using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Biome.Desktop.App.Tray;

/// <summary>
/// Coordinates tray initialization and shutdown within the generic host pipeline.
/// </summary>
public sealed class TrayLifecycleService : IHostedService
{
    private readonly ITrayService _trayService;
    private readonly ILogger<TrayLifecycleService> _logger;

    public TrayLifecycleService(ITrayService trayService, ILogger<TrayLifecycleService> logger)
    {
        _trayService = trayService;
        _logger = logger;
    }

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Starting tray lifecycle service.");
        await _trayService.InitializeAsync(cancellationToken).ConfigureAwait(false);
        _trayService.SetState(TrayIconState.Idle, "Biome Desktop ready");
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Stopping tray lifecycle service.");
        _trayService.SetState(TrayIconState.Idle, "Biome Desktop shutting down");
        return Task.CompletedTask;
    }
}
