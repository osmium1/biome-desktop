using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace Biome.Desktop.Core.Firebase;

public static class FirebaseConfigLoader
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNameCaseInsensitive = true
    };

    public static async Task<FirebaseConfig?> LoadAsync(string? path, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            return null;
        }

        if (!File.Exists(path))
        {
            return null;
        }

        await using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read, 4096, useAsync: true);
        return await JsonSerializer.DeserializeAsync<FirebaseConfig>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false);
    }

    public static IReadOnlyList<string> Validate(FirebaseConfig? config)
    {
        var errors = new List<string>();
        if (config is null)
        {
            errors.Add("config-null");
            return errors;
        }

        if (string.IsNullOrWhiteSpace(config.Web.ProjectId))
        {
            errors.Add("missing-web-project-id");
        }

        if (string.IsNullOrWhiteSpace(config.Web.StorageBucket))
        {
            errors.Add("missing-web-storage-bucket");
        }

        if (string.IsNullOrWhiteSpace(config.ServiceAccount.ProjectId))
        {
            errors.Add("missing-service-account-project-id");
        }

        if (string.IsNullOrWhiteSpace(config.ServiceAccount.PrivateKey))
        {
            errors.Add("missing-service-account-private-key");
        }

        if (string.IsNullOrWhiteSpace(config.ServiceAccount.ClientEmail))
        {
            errors.Add("missing-service-account-client-email");
        }

        if (string.IsNullOrWhiteSpace(config.ServiceAccount.TokenUri))
        {
            errors.Add("missing-service-account-token-uri");
        }

        return errors;
    }
}
