using System.Threading;
using System.Threading.Tasks;

namespace Biome.Desktop.App.Windowing;

public interface IMainWindowController
{
    void Initialize(MainWindow window);
    Task ShowWindowAsync(CancellationToken cancellationToken = default);
    Task HideWindowAsync(CancellationToken cancellationToken = default);
    Task ToggleWindowAsync(CancellationToken cancellationToken = default);
    void ShowSettings();
    bool IsVisible { get; }
}
