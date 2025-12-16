using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Extensions.Logging;
using Wpf.Ui.Controls;

namespace Biome.Desktop.App;

public partial class MainWindow : FluentWindow
{
    private readonly ILogger<MainWindow> _logger;
    private Border? _activeNavItem;

    public MainWindow(ILogger<MainWindow> logger)
    {
        _logger = logger;
        
        InitializeComponent();
        
        _logger.LogInformation("Main window initialized with Biome theme");

        // Navigate to dashboard on load and set it as active
        Loaded += (_, _) =>
        {
            NavigateTo(typeof(Pages.DashboardPage), NavDashboard);
        };
    }

    private void OnNavDashboardClick(object sender, MouseButtonEventArgs e)
    {
        NavigateTo(typeof(Pages.DashboardPage), NavDashboard);
    }

    private void OnNavSettingsClick(object sender, MouseButtonEventArgs e)
    {
        NavigateTo(typeof(Pages.SettingsPage), NavSettings);
    }

    private void NavigateTo(Type pageType, Border navItem)
    {
        // Update active item styling
        if (_activeNavItem != null)
        {
            _activeNavItem.Background = System.Windows.Media.Brushes.Transparent;
            var prevIcon = FindChild<SymbolIcon>(_activeNavItem);
            if (prevIcon != null)
            {
                prevIcon.Foreground = (System.Windows.Media.Brush)FindResource("BiomeTextOnDarkBrush");
            }
        }

        _activeNavItem = navItem;
        navItem.Background = new System.Windows.Media.SolidColorBrush(System.Windows.Media.Color.FromArgb(0x30, 0xFF, 0xFF, 0xFF));
        var activeIcon = FindChild<SymbolIcon>(navItem);
        if (activeIcon != null)
        {
            activeIcon.Foreground = (System.Windows.Media.Brush)FindResource("BiomeSunlightBrush");
        }

        // Navigate
        ContentFrame.Navigate(Activator.CreateInstance(pageType));
        _logger.LogDebug("Navigated to {PageType}", pageType.Name);
    }

    private void OnTitleBarDrag(object sender, MouseButtonEventArgs e)
    {
        if (e.ClickCount == 2)
        {
            WindowState = WindowState == WindowState.Maximized 
                ? WindowState.Normal 
                : WindowState.Maximized;
        }
        else
        {
            DragMove();
        }
    }

    private static T? FindChild<T>(DependencyObject parent) where T : DependencyObject
    {
        if (parent == null) return null;
        int count = VisualTreeHelper.GetChildrenCount(parent);
        for (int i = 0; i < count; i++)
        {
            var child = VisualTreeHelper.GetChild(parent, i);
            if (child is T typed)
                return typed;

            var result = FindChild<T>(child);
            if (result != null)
                return result;
        }
        return null;
    }

    private void OnCloseClick(object sender, MouseButtonEventArgs e)
    {
        Close();
    }

    private void OnCloseButtonEnter(object sender, System.Windows.Input.MouseEventArgs e)
    {
        if (sender is Border border)
        {
            // Slightly darker golden on hover
            border.Background = new System.Windows.Media.SolidColorBrush(
                System.Windows.Media.Color.FromRgb(0xD0, 0x9A, 0x3D));
        }
    }

    private void OnCloseButtonLeave(object sender, System.Windows.Input.MouseEventArgs e)
    {
        if (sender is Border border)
        {
            // Restore original golden color (BiomeSunlight: #E8B54D)
            border.Background = new System.Windows.Media.SolidColorBrush(
                System.Windows.Media.Color.FromRgb(0xE8, 0xB5, 0x4D));
        }
    }
}
