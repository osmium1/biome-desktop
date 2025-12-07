using System;
using System.Threading.Tasks;
using System.Windows;
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

    public IServiceProvider Services => _host.Services;

    public App()
    {
        ShutdownMode = ShutdownMode.OnExplicitShutdown;
        _host = BuildHost();
    }

    private static IHost BuildHost()
    {
        var builder = Host.CreateApplicationBuilder();

        builder.Configuration
            .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true)
            .AddJsonFile($"appsettings.{builder.Environment.EnvironmentName}.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables(prefix: "BIOME__");

        builder.Services.AddHttpClient();
        builder.Services.Configure<BiomeSettings>(builder.Configuration.GetSection("Biome"));

        builder.Services.AddSingleton<MainWindow>();
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

    protected override async void OnStartup(StartupEventArgs e)
    {
        await _host.StartAsync();
        var window = _host.Services.GetRequiredService<MainWindow>();
        MainWindow = window;

        var windowController = _host.Services.GetRequiredService<IMainWindowController>();
        windowController.Initialize(window);
        base.OnStartup(e);
    }

    protected override async void OnExit(ExitEventArgs e)
    {
        await _host.StopAsync();
        _host.Dispose();
        base.OnExit(e);
    }
}
