namespace Biome.Desktop.Core.Configuration;

/// <summary>
/// Represents the Firebase + desktop configuration bindings used by the Windows client.
/// </summary>
public sealed class BiomeSettings
{
    public FirebaseSettings Firebase { get; init; } = new();
    public ClipboardSettings Clipboard { get; init; } = new();

    public sealed class FirebaseSettings
    {
        public string ProjectId { get; init; } = string.Empty;
        public string ServiceAccountPath { get; init; } = string.Empty;
        public string DeviceToken { get; init; } = string.Empty;
        public string StorageBucket { get; init; } = string.Empty;
    }

    public sealed class ClipboardSettings
    {
        public bool AutoQueueFromWatcher { get; init; } = false;
    }
}
