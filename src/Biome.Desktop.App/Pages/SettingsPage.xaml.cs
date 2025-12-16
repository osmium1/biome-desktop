using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Biome.Desktop.App.Configuration;
using Biome.Desktop.App.Windowing;
using Biome.Desktop.Core.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Wpf.Ui.Controls;

namespace Biome.Desktop.App.Pages;

public partial class SettingsPage : Page
{
    private readonly BiomeSettings _settings;
    private readonly UserSettingsStore _userSettings;
    
    private string _originalConfigPath = string.Empty;
    private bool _originalSpeedBoost = true;
    private bool _isLoading = false;

    public SettingsPage()
    {
        InitializeComponent();

        // Resolve the DI graph once up front (needed for options + settings store).
        var services = (System.Windows.Application.Current as App)?.Services;
        var options = services?.GetService<IOptions<BiomeSettings>>();
        _settings = options?.Value ?? new BiomeSettings();
        _userSettings = services?.GetService<UserSettingsStore>() ?? new UserSettingsStore();

        LoadSettings();
    }

    private void LoadSettings()
    {
        _isLoading = true;
        // Device ID is read-only: default to env override else machine name.
        DeviceIdBox.Text = Environment.GetEnvironmentVariable("BIOME_DEVICE_ID") ?? Environment.MachineName;

        var storedPath = _userSettings.LoadFirebaseServiceAccountPath();
        var configPath = !string.IsNullOrWhiteSpace(storedPath)
            ? storedPath
            : _settings.Firebase.ServiceAccountPath;

        if (string.IsNullOrWhiteSpace(configPath))
        {
            var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            configPath = Path.Combine(home, ".biome", "firebase.json");
        }

        ConfigPathBox.Text = configPath;
        SpeedBoostToggle.IsChecked = _userSettings.LoadSpeedBoostEnabled();

        _originalConfigPath = ConfigPathBox.Text;
        _originalSpeedBoost = SpeedBoostToggle.IsChecked ?? true;
        _isLoading = false;
        CheckForChanges();
    }

    // FIX: Manual scroll pumping to fix "dead zones".
    // We capture wheel events at the Page level so controls inside cards cannot swallow them.
    private void OnPageMouseWheel(object sender, MouseWheelEventArgs e)
    {
        if (ContentScroll == null) return;

        // If the scroll viewer can't scroll (not enough content), don't hijack the event.
        if (ContentScroll.ScrollableHeight <= 0) return;

        // Manually scroll. Using 48 as a standard step size.
        double scrollAmount = e.Delta > 0 ? -48 : 48;
        ContentScroll.ScrollToVerticalOffset(ContentScroll.VerticalOffset + scrollAmount);

        // Stop the event so the MainWindow doesn't try to scroll the whole page (Header/Footer)
        e.Handled = true;
    }

    private void OnSettingChanged(object sender, RoutedEventArgs e)
    {
        // Avoid dirty tracking while we populate the initial values.
        if (_isLoading) return;
        CheckForChanges();
    }

    private void CheckForChanges()
    {
        if (UnsavedChangesWarning == null) return;

        var currentPath = ConfigPathBox.Text;
        var currentBoost = SpeedBoostToggle.IsChecked ?? true;

        // When any user-facing field differs from the persisted snapshot, show the warning pill.
        bool isDirty = currentPath != _originalConfigPath || currentBoost != _originalSpeedBoost;
        UnsavedChangesWarning.Visibility = isDirty ? Visibility.Visible : Visibility.Collapsed;
    }

    private void BrowseConfig_Click(object sender, RoutedEventArgs e)
    {
        // Let the user pick the Firebase JSON; keep the owner window consistent so dialogs stay centered.
        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            Filter = "JSON Files (*.json)|*.json|All Files (*.*)|*.*",
            Title = "Select Firebase Service Account JSON"
        };

        var owner = Window.GetWindow(this);
        if (dialog.ShowDialog(owner) == true)
        {
            ConfigPathBox.Text = dialog.FileName;
        }
    }

    private void TestAnimation_Click(object sender, RoutedEventArgs e)
    {
        // Demo the overlay in one-off "demo" mode (single playback).
        new SpeedboostOverlay().StartAnimation(isDemo: true);
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        var path = ConfigPathBox.Text?.Trim();
        if (string.IsNullOrWhiteSpace(path))
        {
            ShowStatus("Path required", "Provide the Firebase service account JSON path before saving.", InfoBarSeverity.Warning);
            ConfigPathBox.Focus();
            return;
        }

        if (!File.Exists(path))
        {
            ShowStatus("File not found", "The specified service account file does not exist.", InfoBarSeverity.Error);
            ConfigPathBox.Focus();
            return;
        }

        try
        {
            _userSettings.SaveFirebaseServiceAccountPath(path);
            _userSettings.SaveSpeedBoostEnabled(SpeedBoostToggle.IsChecked ?? true);
            
            _originalConfigPath = path;
            _originalSpeedBoost = SpeedBoostToggle.IsChecked ?? true;
            CheckForChanges();

            ShowStatus("Saved", "Settings updated successfully.", InfoBarSeverity.Success);
        }
        catch (Exception ex)
        {
            ShowStatus("Save failed", ex.Message, InfoBarSeverity.Error);
        }
    }

    private void Reset_Click(object sender, RoutedEventArgs e)
    {
        // Drop the persisted overrides and repopulate defaults from disk/options.
        _userSettings.Reset();
        LoadSettings();
        ShowStatus("Reset", "User overrides cleared. Defaults restored.", InfoBarSeverity.Informational);
    }

    private void ShowStatus(string title, string message, InfoBarSeverity severity)
    {
        if (StatusInfoBar == null)
        {
            return;
        }

        StatusInfoBar.Title = title;
        StatusInfoBar.Message = message;
        StatusInfoBar.Severity = severity;
        StatusInfoBar.IsOpen = true;
    }
}