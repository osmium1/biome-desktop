using System;
using System.IO;
using System.Text.Json;

namespace Biome.Desktop.App.Configuration;

/// <summary>
/// Handles persistence of user-specific overrides that should not live inside the repo (e.g., Firebase secrets).
/// </summary>
public sealed class UserSettingsStore
{
    private readonly string _filePath;
    private readonly JsonSerializerOptions _serializerOptions = new()
    {
        WriteIndented = true
    };

    public UserSettingsStore()
    {
        var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        if (string.IsNullOrWhiteSpace(home))
        {
            home = AppContext.BaseDirectory;
        }

        var folder = Path.Combine(home, ".biome");
        Directory.CreateDirectory(folder);
        _filePath = Path.Combine(folder, "appsettings.user.json");
    }

    public string? LoadFirebaseServiceAccountPath()
    {
        var model = ReadModel();
        return model?.Biome?.Firebase?.ServiceAccountPath;
    }

    public void SaveFirebaseServiceAccountPath(string? path)
    {
        var model = ReadModel() ?? new UserSettingsModel();
        model.Biome ??= new();
        model.Biome.Firebase ??= new();
        model.Biome.Firebase.ServiceAccountPath = path ?? string.Empty;
        WriteModel(model);
    }

    public void Reset()
    {
        if (File.Exists(_filePath))
        {
            File.Delete(_filePath);
        }
    }

    private UserSettingsModel? ReadModel()
    {
        if (!File.Exists(_filePath))
        {
            return null;
        }

        try
        {
            var json = File.ReadAllText(_filePath);
            return JsonSerializer.Deserialize<UserSettingsModel>(json, _serializerOptions);
        }
        catch
        {
            // If the file is corrupt, ignore it and start fresh when we save next time.
            return null;
        }
    }

    private void WriteModel(UserSettingsModel model)
    {
        var json = JsonSerializer.Serialize(model, _serializerOptions);
        File.WriteAllText(_filePath, json);
    }

    private sealed class UserSettingsModel
    {
        public BiomeSection? Biome { get; set; }

        public sealed class BiomeSection
        {
            public FirebaseSection? Firebase { get; set; }

            public sealed class FirebaseSection
            {
                public string? ProjectId { get; set; }
                public string? ServiceAccountPath { get; set; }
                public string? DeviceToken { get; set; }
                public string? StorageBucket { get; set; }
            }
        }
    }
}
