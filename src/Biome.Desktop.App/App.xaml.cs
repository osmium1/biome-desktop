using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using Biome.Desktop.App.Configuration;
using Biome.Desktop.App.Clipboard;
using Biome.Desktop.App.Dispatch;
using Biome.Desktop.App.Tray;
using Biome.Desktop.App.Windowing;
using Biome.Desktop.App.Transport;
using Biome.Desktop.Core.Firebase;
using Biome.Desktop.Core.Clipboard;
using Biome.Desktop.Core.Configuration;
using Biome.Desktop.Core.Dispatch;
using Biome.Desktop.Core.Transport;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Biome.Desktop.App;

public partial class App : System.Windows.Application
{
    private readonly IHost _host;
    private SpeedboostOverlay? _currentOverlay;

    public IServiceProvider Services => _host.Services;

    public App()
    {
        ShutdownMode = ShutdownMode.OnExplicitShutdown;
        // Capture unhandled exceptions to help diagnose startup crashes
        AppDomain.CurrentDomain.UnhandledException += OnUnhandledException;
        DispatcherUnhandledException += OnDispatcherUnhandledException;
        _host = BuildHost();
    }

    private void OnUnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
        WriteCrash(e.ExceptionObject as Exception, "AppDomain");
    }

    private void OnDispatcherUnhandledException(object sender, System.Windows.Threading.DispatcherUnhandledExceptionEventArgs e)
    {
        WriteCrash(e.Exception, "Dispatcher");
        e.Handled = true;
        Shutdown();
    }

    private static void WriteCrash(Exception? ex, string source)
    {
        try
        {
            var path = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "biome-crash.log");
            var message = $"[{DateTime.Now:u}] ({source}) {ex}\n";
            System.IO.File.AppendAllText(path, message);
        }
        catch
        {
            // ignore logging failures
        }
    }

    private static IHost BuildHost()
    {
        var builder = Host.CreateApplicationBuilder();

        var userConfigPath = ResolveUserConfigPath();

        builder.Configuration
            .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile($"appsettings.{builder.Environment.EnvironmentName}.json", optional: true, reloadOnChange: true);

        if (!string.IsNullOrWhiteSpace(userConfigPath))
        {
            builder.Configuration.AddJsonFile(userConfigPath, optional: true, reloadOnChange: true);
        }

        builder.Configuration.AddEnvironmentVariables(prefix: "BIOME__");

        builder.Services.AddHttpClient();
        builder.Services.Configure<BiomeSettings>(builder.Configuration.GetSection("Biome"));

        builder.Services.AddSingleton<MainWindow>();
        builder.Services.AddSingleton<UserSettingsStore>();
        builder.Services.AddSingleton<ITrayService, TrayService>();
        builder.Services.AddSingleton<IFirebaseTokenProvider, FirebaseTokenProvider>();
        builder.Services.AddSingleton<IMainWindowController, MainWindowController>();
        builder.Services.AddSingleton<IClipboardService, ClipboardService>();
        builder.Services.AddSingleton<IPayloadDispatchQueue, PayloadDispatchQueue>();
        builder.Services.AddSingleton<IPayloadTransport, FirebasePayloadTransport>();
        builder.Services.AddHostedService<TrayLifecycleService>();
        builder.Services.AddHostedService<PayloadDispatchService>();
        builder.Services.AddHostedService<ClipboardWatcherService>();

        builder.Logging.ClearProviders();
        builder.Logging.AddDebug();
        builder.Logging.AddConsole();

        return builder.Build();
    }

    private static string? ResolveUserConfigPath()
    {
        var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        if (string.IsNullOrWhiteSpace(home))
        {
            return null;
        }

        var directory = Path.Combine(home, ".biome");
        Directory.CreateDirectory(directory);
        return Path.Combine(directory, "appsettings.user.json");
    }

    protected override async void OnStartup(StartupEventArgs e)
    {
        await _host.StartAsync();
        var window = _host.Services.GetRequiredService<MainWindow>();
        MainWindow = window;

        var windowController = _host.Services.GetRequiredService<IMainWindowController>();
        windowController.Initialize(window);

        // Hook up SpeedboostOverlay
        var trayService = _host.Services.GetRequiredService<ITrayService>();
        var userSettings = _host.Services.GetRequiredService<UserSettingsStore>();
        
        trayService.StateChanged += (state) =>
        {
            Dispatcher.Invoke(() =>
            {
                if (state == TrayIconState.Sending)
                {
                    if (userSettings.LoadSpeedBoostEnabled())
                    {
                        _currentOverlay?.StopAnimation();
                        _currentOverlay = new SpeedboostOverlay();
                        _currentOverlay.StartAnimation(isDemo: false);
                    }
                }
                else if (state == TrayIconState.Sent || state == TrayIconState.Idle || state == TrayIconState.Error)
                {
                    _currentOverlay?.StopAnimation();
                    _currentOverlay = null;
                }
            });
        };

        base.OnStartup(e);
    }

    protected override async void OnExit(ExitEventArgs e)
    {
        await _host.StopAsync();
        _host.Dispose();
        base.OnExit(e);
    }
}
