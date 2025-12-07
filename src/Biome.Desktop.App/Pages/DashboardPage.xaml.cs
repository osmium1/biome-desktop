using System;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
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

        private void OnRootMouseWheel(object sender, System.Windows.Input.MouseWheelEventArgs e)
        {
            if (ContentScroll != null)
            {
                double offset = ContentScroll.VerticalOffset - e.Delta;
                ContentScroll.ScrollToVerticalOffset(offset);
                e.Handled = true;
            }
        }

        private void OnContentMouseWheel(object sender, System.Windows.Input.MouseWheelEventArgs e)
        {
            if (ContentScroll != null)
            {
                double offset = ContentScroll.VerticalOffset - e.Delta;
                ContentScroll.ScrollToVerticalOffset(offset);
                e.Handled = true;
            }
        }

        private async void OnSendClicked(object sender, RoutedEventArgs e)
        {
            // Resolve the service from the App's service provider
            if (System.Windows.Application.Current is App app)
            {
                var clipboardService = app.Services.GetService<IClipboardService>();
                var dispatchQueue = app.Services.GetService<IPayloadDispatchQueue>();

                if (clipboardService != null && dispatchQueue != null)
                {
                    try
                    {
                        var payload = await clipboardService.CaptureAsync(CancellationToken.None);
                        if (payload != null)
                        {
                            await dispatchQueue.EnqueueAsync(payload, CancellationToken.None);
                            LastShareText.Text = "Just now";
                        }
                    }
                    catch (Exception)
                    {
                        // Ignore for now or show error
                    }
                }
            }
        }
    }
}