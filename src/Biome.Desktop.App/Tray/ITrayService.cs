using System.Threading;
using System.Threading.Tasks;

namespace Biome.Desktop.App.Tray;

public interface ITrayService
{
    Task InitializeAsync(CancellationToken cancellationToken);
    void SetState(TrayIconState state, string? tooltip = null);
}
