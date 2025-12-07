using System;
using System.Collections.Generic;
using System.Drawing;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using System.Windows.Forms;
using Biome.Desktop.App.Windowing;
using Biome.Desktop.Core.Clipboard;
using Biome.Desktop.Core.Dispatch;
using Microsoft.Extensions.Logging;

namespace Biome.Desktop.App.Tray;

/// <summary>
/// Temporary NotifyIcon-based tray while Windows App SDK command surface is under construction.
/// </summary>
public sealed class TrayService : ITrayService, IAsyncDisposable
{
    private readonly ILogger<TrayService> _logger;
    private readonly IClipboardService _clipboardService;
    private readonly IPayloadDispatchQueue _dispatchQueue;
    private readonly IMainWindowController _windowController;
    private readonly Dispatcher _dispatcher;

    private NotifyIcon? _notifyIcon;
    private ContextMenuStrip? _menu;
    private readonly CancellationTokenSource _cts = new();
    private readonly Dictionary<TrayIconState, Icon> _stateIcons;

    public TrayService(
        ILogger<TrayService> logger,
        IClipboardService clipboardService,
        IPayloadDispatchQueue dispatchQueue,
        IMainWindowController windowController)
    {
        _logger = logger;
        _clipboardService = clipboardService;
        _dispatchQueue = dispatchQueue;
        _windowController = windowController;
        _dispatcher = System.Windows.Application.Current?.Dispatcher ?? Dispatcher.CurrentDispatcher;
        _stateIcons = CreateStateIconMap();
    }

    public async Task InitializeAsync(CancellationToken cancellationToken)
    {
        using var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken, _cts.Token);
        await _dispatcher.InvokeAsync(() =>
        {
            _menu = BuildContextMenu();
            _notifyIcon = new NotifyIcon
            {
                Icon = ResolveIcon(TrayIconState.Idle),
                Visible = true,
                Text = "Biome Desktop (Idle)",
                ContextMenuStrip = _menu
            };
            _notifyIcon.MouseClick += OnNotifyIconMouseClick;
        }, DispatcherPriority.Normal, linkedCts.Token).Task.ConfigureAwait(false);

        _logger.LogInformation("Tray service initialized (NotifyIcon placeholder).");
    }

    public void SetState(TrayIconState state, string? tooltip = null)
    {
        _ = _dispatcher.InvokeAsync(() =>
        {
            if (_notifyIcon is null)
            {
                return;
            }

            _notifyIcon.Text = $"Biome Desktop ({state})";
            _notifyIcon.Icon = ResolveIcon(state);

            if (state == TrayIconState.Error && !string.IsNullOrWhiteSpace(tooltip))
            {
                // placeholder for future balloon notifications
            }
        });
    }

    private ContextMenuStrip BuildContextMenu()
    {
        var menu = new ContextMenuStrip();

        var configureItem = new ToolStripMenuItem("Configure Biome");
        configureItem.Click += async (_, _) => await _windowController.ShowWindowAsync(_cts.Token).ConfigureAwait(false);
        menu.Items.Add(configureItem);

        menu.Items.Add(new ToolStripSeparator());

        var sendItem = new ToolStripMenuItem("Send clipboard");
        sendItem.Click += async (_, _) => await HandleSendClipboardAsync().ConfigureAwait(false);
        menu.Items.Add(sendItem);

        menu.Items.Add(new ToolStripSeparator());

        var exitItem = new ToolStripMenuItem("Exit Biome");
        exitItem.Click += (_, _) => _dispatcher.Invoke(() => System.Windows.Application.Current?.Shutdown());
        menu.Items.Add(exitItem);

        return menu;
    }

    private async void OnNotifyIconMouseClick(object? sender, MouseEventArgs e)
    {
        if (e.Button == MouseButtons.Left)
        {
            await HandleSendClipboardAsync().ConfigureAwait(false);
        }
    }

    private async Task HandleSendClipboardAsync()
    {
        try
        {
            SetState(TrayIconState.Sending);
            var payload = await _clipboardService.CaptureAsync(_cts.Token).ConfigureAwait(true);
            
            if (payload is null)
            {
                SetState(TrayIconState.Idle);
                System.Windows.Forms.MessageBox.Show("Clipboard is empty or contains unsupported content.", "Biome Desktop", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            await _dispatchQueue.EnqueueAsync(payload, _cts.Token).ConfigureAwait(true);
            SetState(TrayIconState.Waiting);
            // Success is silent (icon change only)
        }
        catch (OperationCanceledException)
        {
            // shutting down; nothing to log.
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Tray send clipboard command failed.");
            SetState(TrayIconState.Error);
            System.Windows.Forms.MessageBox.Show($"Send failed: {ex.Message}", "Biome Desktop Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    public ValueTask DisposeAsync()
    {
        _cts.Cancel();
        if (_notifyIcon != null)
        {
            _dispatcher.Invoke(() =>
            {
                _notifyIcon.Visible = false;
                _notifyIcon.Dispose();
                _menu?.Dispose();
            });
        }

        foreach (var icon in _stateIcons.Values)
        {
            icon.Dispose();
        }

        _cts.Dispose();
        return ValueTask.CompletedTask;
    }

    private static Dictionary<TrayIconState, Icon> CreateStateIconMap()
    {
        // Helper to draw simple colored circles/shapes as icons
        Icon DrawIcon(Color color, string text)
        {
            using var bitmap = new Bitmap(16, 16);
            using var g = Graphics.FromImage(bitmap);
            g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
            
            // Draw background circle
            using var brush = new SolidBrush(color);
            g.FillEllipse(brush, 1, 1, 14, 14);
            
            // Draw text/symbol
            if (!string.IsNullOrEmpty(text))
            {
                using var font = new Font(new FontFamily("Segoe UI"), 8, System.Drawing.FontStyle.Bold);
                var size = g.MeasureString(text, font);
                g.DrawString(text, font, Brushes.White, (16 - size.Width) / 2, (16 - size.Height) / 2);
            }
            
            return Icon.FromHandle(bitmap.GetHicon());
        }

        return new Dictionary<TrayIconState, Icon>
        {
            [TrayIconState.Idle] = DrawIcon(Color.FromArgb(0, 120, 215), "B"), // Blue 'B'
            [TrayIconState.Waiting] = DrawIcon(Color.Orange, "…"), // Orange ellipsis
            [TrayIconState.Sending] = DrawIcon(Color.Purple, "↑"), // Purple arrow
            [TrayIconState.Sent] = DrawIcon(Color.Green, "✓"), // Green check
            [TrayIconState.Error] = DrawIcon(Color.Red, "!") // Red bang
        };
    }

    private Icon ResolveIcon(TrayIconState state)
    {
        if (_stateIcons.TryGetValue(state, out var icon))
        {
            return icon;
        }

        return _stateIcons[TrayIconState.Idle];
    }
}
