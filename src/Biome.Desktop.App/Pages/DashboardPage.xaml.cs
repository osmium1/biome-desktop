using System;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Biome.Desktop.Core.Clipboard;
using Biome.Desktop.Core.Dispatch;
using Microsoft.Extensions.DependencyInjection;

namespace Biome.Desktop.App.Pages
{
    public partial class DashboardPage : Page
    {
        public DashboardPage()
        {
            InitializeComponent();
        }

        // FIX: Shared robust scroll logic — mirror the Settings page behavior so cards scroll even when focused.
        private void OnPageMouseWheel(object sender, MouseWheelEventArgs e)
        {
            if (ContentScroll == null) return;

            double scrollAmount = e.Delta > 0 ? -48 : 48;
            ContentScroll.ScrollToVerticalOffset(ContentScroll.VerticalOffset + scrollAmount);

            e.Handled = true;
        }

        private async void OnSendClicked(object sender, RoutedEventArgs e)
        {
            // Resolve services from the App host so this page stays dumb/passive.
            if (System.Windows.Application.Current is App app)
            {
                var clipboardService = app.Services.GetService<IClipboardService>();
                var dispatchQueue = app.Services.GetService<IPayloadDispatchQueue>();

                if (clipboardService != null && dispatchQueue != null)
                {
                    try
                    {
                        // Capture the current clipboard and enqueue the payload so background dispatch can ship it.
                        var payload = await clipboardService.CaptureAsync(CancellationToken.None);
                        if (payload != null)
                        {
                            await dispatchQueue.EnqueueAsync(payload, CancellationToken.None);
                            LastShareText.Text = "Just now";
                        }
                    }
                    catch (Exception)
                    {
                        // Ignore for now — errors get surfaced in diagnostics panes later.
                    }
                }
            }
        }
    }
}