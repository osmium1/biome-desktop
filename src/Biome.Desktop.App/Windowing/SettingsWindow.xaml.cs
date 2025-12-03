using System;
using System.Windows;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Options;
using Biome.Desktop.Core.Configuration;
using Wpf.Ui.Controls;

namespace Biome.Desktop.App.Windowing;

public partial class SettingsWindow : FluentWindow
{
    private readonly BiomeSettings _settings;

    public SettingsWindow(IOptions<BiomeSettings> settings)
    {
        InitializeComponent();
        _settings = settings.Value;
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
        // In a real app, we'd write to appsettings.json or a user override file.
        // For now, we'll just show a message that this requires manual config or env vars,
        // as we haven't implemented a writable settings store yet.
        
        System.Windows.MessageBox.Show("Settings saving is not yet fully implemented. Please configure via 'appsettings.json' or Environment Variables for now.", 
                        "Not Implemented", System.Windows.MessageBoxButton.OK, MessageBoxImage.Information);
        
        // Ideally: _settingsStore.Update(s => s.Firebase.ServiceAccountPath = ConfigPathBox.Text);
        Close();
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        Close();
    }
}
