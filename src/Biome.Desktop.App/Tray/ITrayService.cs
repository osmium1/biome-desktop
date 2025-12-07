using System;
using System.Threading;
using System.Threading.Tasks;

namespace Biome.Desktop.App.Tray;

public interface ITrayService
{
    event Action<TrayIconState> StateChanged;
    Task InitializeAsync(CancellationToken cancellationToken);
    void SetState(TrayIconState state, string? tooltip = null);
}
