using System;
using System.Windows;
using Biome.Desktop.App.Windowing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Wpf.Ui.Controls;

namespace Biome.Desktop.App;

public partial class MainWindow : FluentWindow
{
    private readonly ILogger<MainWindow> _logger;
    private readonly IServiceProvider _serviceProvider;

    public MainWindow(
        ILogger<MainWindow> logger,
        IServiceProvider serviceProvider)
    {
        _logger = logger;
        _serviceProvider = serviceProvider;
        
        InitializeComponent();
        
        _logger.LogInformation("Main window initialized");

        // Configure Navigation
        RootNavigation.Loaded += (sender, args) =>
        {
            RootNavigation.Navigate(typeof(Pages.DashboardPage));
        };
    }

    private void OnSettingsClicked(object sender, RoutedEventArgs e)
    {
        // Open the Settings Window
        var settingsWindow = _serviceProvider.GetService<SettingsWindow>();
        if (settingsWindow != null)
        {
            settingsWindow.Show();
            settingsWindow.Activate();
        }
    }
}
