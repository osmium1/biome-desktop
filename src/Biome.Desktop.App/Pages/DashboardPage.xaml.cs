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
            DeviceNameText.Text = Environment.MachineName;
        }

        private async void OnSendClicked(object sender, MouseButtonEventArgs e)
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
                            StatusSubtitle.Text = "Content sent successfully";
                        }
                        else
                        {
                            LastShareText.Text = "Clipboard empty";
                            StatusSubtitle.Text = "No content to send";
                        }
                    }
                    catch (Exception ex)
                    {
                        LastShareText.Text = "Failed";
                        StatusSubtitle.Text = $"Error: {ex.Message}";
                    }
                }
            }
        }
    }
}