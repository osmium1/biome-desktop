using System;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using Microsoft.Extensions.Logging;

using Microsoft.Extensions.Options;
using Biome.Desktop.Core.Configuration;

namespace Biome.Desktop.App.Windowing;

public sealed class MainWindowController : IMainWindowController
{
    private readonly ILogger<MainWindowController> _logger;
    private readonly IServiceProvider _serviceProvider;
    private MainWindow? _window;
    private bool _isShuttingDown;
    private bool _isVisible;

    public MainWindowController(ILogger<MainWindowController> logger, IServiceProvider serviceProvider)
    {
        _logger = logger;
        _serviceProvider = serviceProvider;
    }

    public bool IsVisible => _isVisible;

    public void Initialize(MainWindow window)
    {
        if (window is null)
        {
            throw new ArgumentNullException(nameof(window));
        }

        if (_window != null)
        {
            return;
        }

        _window = window;
        _window.Closing += OnWindowClosing;
        _window.Dispatcher.ShutdownStarted += (_, _) => _isShuttingDown = true;
        _logger.LogInformation("Main window controller initialized.");
        _window.Hide();
        _isVisible = false;
    }

    public void ShowSettings()
    {
        _window?.Dispatcher.Invoke(() =>
        {
            // Resolve settings via DI manually since we don't have constructor injection for the window here easily
            // or we can just instantiate it if we pass dependencies.
            // For simplicity in this phase, we'll use the service provider.
            var settings = _serviceProvider.GetService(typeof(IOptions<BiomeSettings>)) as IOptions<BiomeSettings>;
            if (settings != null)
            {
                var settingsWindow = new SettingsWindow(settings);
                settingsWindow.Show();
                settingsWindow.Activate();
            }
        });
    }

    public Task ShowWindowAsync(CancellationToken cancellationToken = default)
    {
        if (_window is null)
        {
            return Task.CompletedTask;
        }

        return _window.Dispatcher.InvokeAsync(() =>
        {
            if (!_window.IsVisible)
            {
                _window.Show();
            }

            if (_window.WindowState == WindowState.Minimized)
            {
                _window.WindowState = WindowState.Normal;
            }

            _window.Activate();
            _window.Topmost = true;
            _window.Topmost = false;
            _window.Focus();
            _isVisible = true;
        }, DispatcherPriority.Normal, cancellationToken).Task;
    }

    public Task HideWindowAsync(CancellationToken cancellationToken = default)
    {
        if (_window is null)
        {
            return Task.CompletedTask;
        }

        return _window.Dispatcher.InvokeAsync(() =>
        {
            _window.Hide();
            _isVisible = false;
        }, DispatcherPriority.Background, cancellationToken).Task;
    }

    public async Task ToggleWindowAsync(CancellationToken cancellationToken = default)
    {
        if (_window is null)
        {
            return;
        }

        if (_window.IsVisible)
        {
            await HideWindowAsync(cancellationToken).ConfigureAwait(false);
        }
        else
        {
            await ShowWindowAsync(cancellationToken).ConfigureAwait(false);
        }
    }

    private async void OnWindowClosing(object? sender, CancelEventArgs e)
    {
        if (_isShuttingDown)
        {
            return;
        }

        e.Cancel = true;
        await HideWindowAsync().ConfigureAwait(false);
        _logger.LogInformation("Main window hidden instead of closed.");
    }
}
