using System;
using System.Windows;
using Biome.Desktop.App.Windowing;
using Microsoft.Extensions.Logging;
using Wpf.Ui.Controls;

namespace Biome.Desktop.App;

public partial class MainWindow : FluentWindow
{
    private readonly ILogger<MainWindow> _logger;

    public MainWindow(ILogger<MainWindow> logger)
    {
        _logger = logger;
        
        InitializeComponent();
        
        _logger.LogInformation("Main window initialized");

        // Configure Navigation
        RootNavigation.Loaded += (sender, args) =>
        {
            RootNavigation.Navigate(typeof(Pages.DashboardPage));
        };
    }

}
