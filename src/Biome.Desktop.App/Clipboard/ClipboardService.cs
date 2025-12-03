using System;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using System.IO;
using System.Windows.Media.Imaging;
using Biome.Desktop.Core.Clipboard;
using Biome.Desktop.Core.Payloads;
using Microsoft.Extensions.Logging;

namespace Biome.Desktop.App.Clipboard;

/// <summary>
/// Wraps the Win32 clipboard APIs exposed through WPF to capture text payloads on the UI dispatcher.
/// </summary>
public sealed class ClipboardService : IClipboardService
{
    private readonly ILogger<ClipboardService> _logger;
    private readonly Dispatcher _dispatcher;

    public ClipboardService(ILogger<ClipboardService> logger)
    {
        _logger = logger;
        _dispatcher = System.Windows.Application.Current?.Dispatcher ?? Dispatcher.CurrentDispatcher;
    }

    public async Task<ClipboardPayload?> CaptureAsync(CancellationToken cancellationToken)
    {
        return await _dispatcher.InvokeAsync(() =>
        {
            try
            {
                if (System.Windows.Clipboard.ContainsImage())
                {
                    var image = System.Windows.Clipboard.GetImage();
                    if (image != null)
                    {
                        byte[] imageBytes;
                        using (var ms = new MemoryStream())
                        {
                            var encoder = new PngBitmapEncoder();
                            encoder.Frames.Add(BitmapFrame.Create(image));
                            encoder.Save(ms);
                            imageBytes = ms.ToArray();
                        }

                        var payload = new ClipboardPayload(
                            Guid.NewGuid().ToString("n"),
                            ClipboardPayloadKind.Image,
                            null,
                            DateTimeOffset.UtcNow,
                            Environment.MachineName,
                            imageBytes);

                        _logger.LogInformation("Captured clipboard image payload {PayloadId} with {Bytes} bytes.", payload.Id, imageBytes.Length);
                        return payload;
                    }
                }

                if (System.Windows.Clipboard.ContainsText())
                {
                    var text = System.Windows.Clipboard.GetText(System.Windows.TextDataFormat.UnicodeText);
                    if (!string.IsNullOrWhiteSpace(text))
                    {
                        var payload = new ClipboardPayload(
                            Guid.NewGuid().ToString("n"),
                            ClipboardPayloadKind.Text,
                            text,
                            DateTimeOffset.UtcNow,
                            Environment.MachineName);

                        _logger.LogInformation("Captured clipboard text payload {PayloadId} with {Length} chars.", payload.Id, text.Length);
                        return payload;
                    }
                }

                _logger.LogWarning("Clipboard does not contain supported content (Text or Image).");
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to capture clipboard contents.");
                return null;
            }
        }, DispatcherPriority.Send, cancellationToken);
    }
}
