using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Controls.Primitives;
using Biome.Desktop.App.Windowing;
using Microsoft.Extensions.Logging;
using Wpf.Ui.Controls;
using Button = System.Windows.Controls.Button;

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
            RootNavigation.IsPaneOpen = false;
            HidePaneToggles();
            RootNavigation.Navigate(typeof(Pages.DashboardPage));
        };

        RootNavigation.LayoutUpdated += (_, _) =>
        {
            HidePaneToggles();
            RootNavigation.IsPaneOpen = false;
        };

        RootNavigation.PreviewMouseDown += OnNavPreviewMouseDown;
    }

    private void OnNavPreviewMouseDown(object sender, MouseButtonEventArgs e)
    {
        // Swallow clicks on the pane toggle to prevent expansion
        if (e.OriginalSource is DependencyObject source)
        {
            var toggle = FindParent<ToggleButton>(source);
            var buttonToggle = FindParent<Button>(source);
            if (toggle != null || buttonToggle != null)
            {
                HidePaneToggles();
                RootNavigation.IsPaneOpen = false;
                e.Handled = true;
            }
        }
    }

    private void HidePaneToggles()
    {
        foreach (var toggle in FindChildren<ToggleButton>(RootNavigation))
        {
            StripToggleVisual(toggle);
        }

        // Fallback: some templates may use Button instead of ToggleButton
        foreach (var button in FindChildren<System.Windows.Controls.Button>(RootNavigation))
        {
            if (IsPaneToggleName(button.Name))
            {
                StripButtonVisual(button);
            }
        }
    }

    private static void StripToggleVisual(ToggleButton toggle)
    {
        toggle.Visibility = Visibility.Collapsed;
        toggle.IsEnabled = false;
        toggle.IsHitTestVisible = false;
        toggle.Opacity = 0;
        toggle.Width = 0;
        toggle.Height = 0;
        toggle.Margin = new Thickness(0);
        toggle.Padding = new Thickness(0);
        toggle.Template = new ControlTemplate(typeof(ToggleButton));
    }

    private static T? FindChild<T>(DependencyObject parent, string childName) where T : FrameworkElement
    {
        if (parent == null) return null;
        int count = VisualTreeHelper.GetChildrenCount(parent);
        for (int i = 0; i < count; i++)
        {
            var child = VisualTreeHelper.GetChild(parent, i);
            if (child is T typed && (string.IsNullOrEmpty(childName) || typed.Name == childName))
                return typed;

            var result = FindChild<T>(child, childName);
            if (result != null)
                return result;
        }
        return null;
    }

    private static IEnumerable<T> FindChildren<T>(DependencyObject parent) where T : FrameworkElement
    {
        if (parent == null)
            yield break;

        int count = VisualTreeHelper.GetChildrenCount(parent);
        for (int i = 0; i < count; i++)
        {
            var child = VisualTreeHelper.GetChild(parent, i);
            if (child is T typed)
                yield return typed;

            foreach (var descendant in FindChildren<T>(child))
                yield return descendant;
        }
    }

    private static void StripButtonVisual(System.Windows.Controls.Button button)
    {
        button.Visibility = Visibility.Collapsed;
        button.IsEnabled = false;
        button.IsHitTestVisible = false;
        button.Opacity = 0;
        button.Width = 0;
        button.Height = 0;
        button.Margin = new Thickness(0);
        button.Padding = new Thickness(0);
        button.Template = new ControlTemplate(typeof(Button));
    }

    private static bool IsPaneToggleName(string name)
    {
        if (string.IsNullOrWhiteSpace(name)) return false;
        var lowered = name.ToLowerInvariant();
        return lowered.Contains("toggle") || lowered.Contains("pane");
    }

    private static T? FindParent<T>(DependencyObject child) where T : DependencyObject
    {
        var current = VisualTreeHelper.GetParent(child);
        while (current != null)
        {
            if (current is T typed)
                return typed;
            current = VisualTreeHelper.GetParent(current);
        }
        return null;
    }

}
