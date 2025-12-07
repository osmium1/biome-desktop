using System;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using Microsoft.Extensions.Logging;

namespace Biome.Desktop.App.Windowing;

public sealed class MainWindowController : IMainWindowController
{
    private readonly ILogger<MainWindowController> _logger;
    private MainWindow? _window;
    private bool _isShuttingDown;
    private bool _isVisible;

    public MainWindowController(ILogger<MainWindowController> logger)
    {
        _logger = logger;
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
