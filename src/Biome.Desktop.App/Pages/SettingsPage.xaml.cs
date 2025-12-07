using System;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using Biome.Desktop.Core.Configuration;

namespace Biome.Desktop.App.Pages;

public partial class SettingsPage : Page
{
    private readonly BiomeSettings _settings;

    public SettingsPage()
    {
        InitializeComponent();

        var options = (System.Windows.Application.Current as App)?.Services.GetService<IOptions<BiomeSettings>>();
        _settings = options?.Value ?? new BiomeSettings();

        LoadSettings();
    }

    private void LoadSettings()
    {
        DeviceIdBox.Text = Environment.GetEnvironmentVariable("BIOME_DEVICE_ID") ?? Environment.MachineName;

        var configPath = _settings.Firebase.ServiceAccountPath;
        if (string.IsNullOrWhiteSpace(configPath))
        {
            var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            configPath = System.IO.Path.Combine(home, ".biome", "firebase.json");
        }

        ConfigPathBox.Text = configPath;
    }

    private void BrowseConfig_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new Microsoft.Win32.OpenFileDialog
        {
            Filter = "JSON Files (*.json)|*.json|All Files (*.*)|*.*",
            Title = "Select Firebase Service Account JSON"
        };

        if (dialog.ShowDialog() == true)
        {
            ConfigPathBox.Text = dialog.FileName;
        }
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        System.Windows.MessageBox.Show(
            "Settings saving is not yet fully implemented. Please configure via 'appsettings.json' or Environment Variables for now.",
            "Not Implemented",
            MessageBoxButton.OK,
            MessageBoxImage.Information);

        NavigationService?.GoBack();
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        NavigationService?.GoBack();
    }
}
