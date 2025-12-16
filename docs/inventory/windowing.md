# Windowing + Navigation

The console window is intentionally hidden by default and only exposed when the user opens it from the tray. This document outlines the relevant pieces.

## `MainWindow`
`MainWindow.xaml` uses the `Wpf.Ui` Fluent shell with a `NavigationView` hosting `DashboardPage` (and a disabled History placeholder).

```xml
<ui:FluentWindow ... Title="Biome Desktop" WindowBackdropType="Mica" ExtendsContentIntoTitleBar="True">
    <Grid>
        <ui:TitleBar Title="Biome Desktop" />
        <ui:NavigationView x:Name="RootNavigation">
            <ui:NavigationView.MenuItems>
                <ui:NavigationViewItem Content="Dashboard" TargetPageType="{x:Type pages:DashboardPage}" />
                <ui:NavigationViewItem Content="History" IsEnabled="False" />
            </ui:NavigationView.MenuItems>
            <ui:NavigationView.FooterMenuItems>
                <ui:NavigationViewItem Content="Settings" Click="OnSettingsClicked" />
            </ui:NavigationView.FooterMenuItems>
            <Frame x:Name="RootFrame" />
        </ui:NavigationView>
    </Grid>
</ui:FluentWindow>
```

Code-behind wires a default navigation target and opens the settings window via the service provider:

```csharp
public MainWindow(ILogger<MainWindow> logger, IServiceProvider serviceProvider)
{
    InitializeComponent();
    RootNavigation.Loaded += (_, _) => RootNavigation.Navigate(typeof(Pages.DashboardPage));
}

private void OnSettingsClicked(object sender, RoutedEventArgs e)
{
    var settingsWindow = _serviceProvider.GetService<SettingsWindow>();
    settingsWindow?.Show();
    settingsWindow?.Activate();
}
```

## `MainWindowController`
Registered as `IMainWindowController`, this class keeps the UI hidden and exposes async helpers for the tray.

```csharp
public void Initialize(MainWindow window)
{
    _window = window;
    _window.Closing += OnWindowClosing; // hides instead of closes
    _window.Dispatcher.ShutdownStarted += (_, _) => _isShuttingDown = true;
    _window.Hide();
    _isVisible = false;
}

public Task ToggleWindowAsync(CancellationToken cancellationToken = default)
{
    if (_window.IsVisible)
    {
        return HideWindowAsync(cancellationToken);
    }
    else
    {
        return ShowWindowAsync(cancellationToken);
    }
}
```

`ShowSettings()` currently bypasses DI and instantiates `SettingsWindow` manually because the controller lacks constructor injection for it.

### Settings window
`SettingsWindow.xaml` renders read-only device info and a browse button for the Firebase service account path. The code-behind shows a message box instead of persisting changes:

```csharp
private void Save_Click(object sender, RoutedEventArgs e)
{
    MessageBox.Show(
        "Settings saving is not yet fully implemented. Please configure via appsettings.json or Environment Variables for now.",
        "Not Implemented",
        MessageBoxButton.OK,
        MessageBoxImage.Information);
    Close();
}
```

Idle work:
- `ui:ToggleSwitch` for "Auto-Send Clipboard" is disabled; wiring it to `BiomeSettings.Clipboard.AutoQueueFromWatcher` would make it actionable.
- No validation occurs when browsing for the Firebase JSON; user input is not persisted anywhere.

## `DashboardPage`
`DashboardPage.xaml` provides a quick action tile that triggers clipboard capture. It resolves services directly from the `App` singleton rather than using MVVM bindings yet.

```csharp
private async void OnSendClicked(object sender, RoutedEventArgs e)
{
    if (System.Windows.Application.Current is App app)
    {
        var clipboardService = app.Services.GetService<IClipboardService>();
        var dispatchQueue = app.Services.GetService<IPayloadDispatchQueue>();

        var payload = await clipboardService!.CaptureAsync(CancellationToken.None);
        if (payload != null)
        {
            await dispatchQueue!.EnqueueAsync(payload, CancellationToken.None);
            LastSyncText.Text = "Just now";
        }
    }
}
```

Since the dashboard bypasses the tray state machine, the tray icon does not indicate activity when sending via the page—only the local "Last Sync" label updates. A shared status service would help keep UX consistent.
