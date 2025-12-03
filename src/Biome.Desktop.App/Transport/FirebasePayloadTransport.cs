using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Biome.Desktop.Core.Configuration;
using Biome.Desktop.Core.Firebase;
using Biome.Desktop.Core.Payloads;
using Biome.Desktop.Core.Transport;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Biome.Desktop.App.Transport;

/// <summary>
/// Placeholder Firebase transport that will eventually upload to Storage + Firestore and trigger FCM.
/// </summary>
public sealed class FirebasePayloadTransport : IPayloadTransport, IDisposable
{
    private readonly ILogger<FirebasePayloadTransport> _logger;
    private readonly BiomeSettings _settings;
    private readonly IFirebaseTokenProvider _tokenProvider;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly string _outboxDirectory;
    private readonly JsonSerializerOptions _serializerOptions;
    private readonly SemaphoreSlim _configLock = new(1, 1);
    private FirebaseConfig? _cachedConfig;
    private string? _cachedConfigPath;

    public FirebasePayloadTransport(
        IOptions<BiomeSettings> settings,
        IFirebaseTokenProvider tokenProvider,
        IHttpClientFactory httpClientFactory,
        ILogger<FirebasePayloadTransport> logger)
    {
        _settings = settings.Value;
        _tokenProvider = tokenProvider;
        _httpClientFactory = httpClientFactory;
        _logger = logger;
        _outboxDirectory = ResolveOutboxDirectory();
        Directory.CreateDirectory(_outboxDirectory);
        _serializerOptions = new JsonSerializerOptions(JsonSerializerDefaults.Web)
        {
            WriteIndented = true
        };
    }

    public async Task SendAsync(ClipboardPayload payload, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        if (!TryBuildTransportContent(payload, out var envelope, out var reason))
        {
            await WriteOutboxEnvelopeAsync(payload, reason, null, cancellationToken).ConfigureAwait(false);
            return;
        }

        var configPath = ResolveServiceAccountPath();
        if (!File.Exists(configPath))
        {
            await WriteOutboxEnvelopeAsync(payload, "service-account-file-not-found", new Dictionary<string, object?>
            {
                ["path"] = configPath
            }, cancellationToken).ConfigureAwait(false);
            return;
        }

        var config = await GetFirebaseConfigAsync(configPath, cancellationToken).ConfigureAwait(false);
        if (config is null)
        {
            await WriteOutboxEnvelopeAsync(payload, "firebase-config-load-failed", new Dictionary<string, object?>
            {
                ["path"] = configPath
            }, cancellationToken).ConfigureAwait(false);
            return;
        }

        var validationErrors = FirebaseConfigLoader.Validate(config);
        if (validationErrors.Count > 0)
        {
            await WriteOutboxEnvelopeAsync(payload, "firebase-config-invalid", new Dictionary<string, object?>
            {
                ["errors"] = validationErrors
            }, cancellationToken).ConfigureAwait(false);
            return;
        }

        var token = await _tokenProvider.GetAccessTokenAsync(config, cancellationToken).ConfigureAwait(false);
        if (token is null)
        {
            await WriteOutboxEnvelopeAsync(payload, "firebase-token-unavailable", null, cancellationToken).ConfigureAwait(false);
            return;
        }

        var accountId = ResolveAccountId(config);
        var deviceId = ResolveDeviceId();
        var clipId = Guid.NewGuid().ToString("n");
        var storagePath = $"clips/{accountId}/{clipId}.json";
        var httpClient = _httpClientFactory.CreateClient("FirebaseTransport");

        try
        {
            var uploadResult = await UploadPayloadAsync(httpClient, token.Token, config.Web.StorageBucket, storagePath, envelope, cancellationToken).ConfigureAwait(false);
            await CreateFirestoreDocumentAsync(httpClient, token.Token, config.Web.ProjectId, accountId, clipId, storagePath, deviceId, uploadResult, envelope.Kind, envelope.Metadata, cancellationToken).ConfigureAwait(false);

            var fcmToken = ResolveFcmToken();
            if (!string.IsNullOrWhiteSpace(fcmToken))
            {
                await SendFcmNotificationAsync(httpClient, token.Token, config.Web.ProjectId, fcmToken, clipId, accountId, storagePath, envelope.Kind, cancellationToken).ConfigureAwait(false);
            }

            _logger.LogInformation("Uploaded payload {PayloadId} -> {StoragePath}", payload.Id, storagePath);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Firebase transport failed for payload {PayloadId}", payload.Id);
            await WriteOutboxEnvelopeAsync(payload, "firebase-send-error", new Dictionary<string, object?>
            {
                ["storagePath"] = storagePath,
                ["exception"] = ex.Message
            }, cancellationToken).ConfigureAwait(false);
        }
    }

    private async Task<FirebaseConfig?> GetFirebaseConfigAsync(string path, CancellationToken cancellationToken)
    {
        if (_cachedConfig is not null && string.Equals(_cachedConfigPath, path, StringComparison.OrdinalIgnoreCase))
        {
            return _cachedConfig;
        }

        await _configLock.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (_cachedConfig is not null && string.Equals(_cachedConfigPath, path, StringComparison.OrdinalIgnoreCase))
            {
                return _cachedConfig;
            }

            FirebaseConfig? config;
            try
            {
                config = await FirebaseConfigLoader.LoadAsync(path, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to parse firebase config at {Path}.", path);
                return null;
            }
            _cachedConfig = config;
            _cachedConfigPath = path;
            return config;
        }
        finally
        {
            _configLock.Release();
        }
    }

    private async Task WriteOutboxEnvelopeAsync(ClipboardPayload payload, string reason, IReadOnlyDictionary<string, object?>? context, CancellationToken cancellationToken)
    {
        var envelope = new OutboxEnvelope(
            Guid.NewGuid().ToString("n"),
            payload.Id,
            reason,
            DateTimeOffset.UtcNow,
            payload,
            context);

        var filePath = Path.Combine(_outboxDirectory, $"{envelope.EnvelopeId}.json");

        try
        {
            await using var fileStream = new FileStream(
                filePath,
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.None,
                4096,
                useAsync: true);
            await JsonSerializer.SerializeAsync(fileStream, envelope, _serializerOptions, cancellationToken).ConfigureAwait(false);
            _logger.LogInformation("Payload {PayloadId} recorded in outbox ({FilePath}) with reason {Reason}.", payload.Id, filePath, reason);
        }
        catch (IOException ex)
        {
            _logger.LogError(ex, "Failed to write payload {PayloadId} to outbox path {FilePath}.", payload.Id, filePath);
            throw;
        }
    }

    private bool TryBuildTransportContent(ClipboardPayload payload, out StorageEnvelope envelope, out string reason)
    {
        if (payload.Kind == ClipboardPayloadKind.Text)
        {
            if (string.IsNullOrWhiteSpace(payload.TextContent))
            {
                envelope = default;
                reason = "empty-text-payload";
                return false;
            }

            var metadata = new Dictionary<string, object?>
            {
                ["capturedAtUtc"] = payload.CapturedAtUtc,
                ["sourceApplication"] = payload.SourceApplication,
                ["length"] = payload.TextContent.Length
            };

            envelope = new StorageEnvelope(
                Kind: "text",
                Data: payload.TextContent,
                Metadata: JsonSerializer.Serialize(metadata, _serializerOptions),
                Version: 1,
                SentAtSeconds: DateTimeOffset.UtcNow.ToUnixTimeSeconds());
            reason = string.Empty;
            return true;
        }
        else if (payload.Kind == ClipboardPayloadKind.Image)
        {
            if (payload.ImageBytes is null || payload.ImageBytes.Length == 0)
            {
                envelope = default;
                reason = "empty-image-payload";
                return false;
            }

            var metadata = new Dictionary<string, object?>
            {
                ["capturedAtUtc"] = payload.CapturedAtUtc,
                ["sourceApplication"] = payload.SourceApplication,
                ["sizeBytes"] = payload.ImageBytes.Length,
                ["format"] = "png"
            };

            envelope = new StorageEnvelope(
                Kind: "image",
                Data: Convert.ToBase64String(payload.ImageBytes),
                Metadata: JsonSerializer.Serialize(metadata, _serializerOptions),
                Version: 1,
                SentAtSeconds: DateTimeOffset.UtcNow.ToUnixTimeSeconds());
            reason = string.Empty;
            return true;
        }

        envelope = default;
        reason = "unsupported-payload-kind";
        return false;
    }

    private async Task<StorageUploadResult> UploadPayloadAsync(
        HttpClient client,
        string accessToken,
        string bucket,
        string storagePath,
        StorageEnvelope envelope,
        CancellationToken cancellationToken)
    {
        var url = $"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o?uploadType=media&name={Uri.EscapeDataString(storagePath)}";
        using var request = new HttpRequestMessage(HttpMethod.Post, url)
        {
            Content = new StringContent(JsonSerializer.Serialize(envelope, _serializerOptions), Encoding.UTF8, "application/json")
        };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

        var response = await client.SendAsync(request, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
        await using var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
        var uploadResult = await JsonSerializer.DeserializeAsync<StorageUploadResult>(stream, _serializerOptions, cancellationToken).ConfigureAwait(false);
        return uploadResult;
    }

    private async Task CreateFirestoreDocumentAsync(
        HttpClient client,
        string accessToken,
        string projectId,
        string accountId,
        string clipId,
        string storagePath,
        string deviceId,
        StorageUploadResult uploadResult,
        string kind,
        string metadataJson,
        CancellationToken cancellationToken)
    {
        var url = $"https://firestore.googleapis.com/v1/projects/{projectId}/databases/(default)/documents/accounts/{accountId}/clips?documentId={clipId}";
        var document = new FirestoreDocumentRequest
        {
            Fields = new Dictionary<string, FirestoreValue>
            {
                ["storagePath"] = FirestoreValue.String(storagePath),
                ["kind"] = FirestoreValue.String(kind),
                ["metadata"] = FirestoreValue.String(metadataJson),
                ["senderDeviceId"] = FirestoreValue.String(deviceId),
                ["status"] = FirestoreValue.String("queued"),
                ["bucketGeneration"] = FirestoreValue.String(uploadResult.Generation ?? string.Empty),
                ["createdAt"] = FirestoreValue.Timestamp(DateTimeOffset.UtcNow)
            }
        };

        using var request = new HttpRequestMessage(HttpMethod.Post, url)
        {
            Content = new StringContent(JsonSerializer.Serialize(document, _serializerOptions), Encoding.UTF8, "application/json")
        };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

        var response = await client.SendAsync(request, cancellationToken).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
    }

    private async Task SendFcmNotificationAsync(
        HttpClient client,
        string accessToken,
        string projectId,
        string deviceToken,
        string clipId,
        string accountId,
        string storagePath,
        string kind,
        CancellationToken cancellationToken)
    {
        var url = $"https://fcm.googleapis.com/v1/projects/{projectId}/messages:send";
        var requestBody = new FcmRequest
        {
            Message = new FcmMessage
            {
                Token = deviceToken,
                Data = new Dictionary<string, string>
                {
                    ["clip_id"] = clipId,
                    ["account_id"] = accountId,
                    ["kind"] = kind,
                    ["storage_path"] = storagePath
                }
            }
        };

        using var request = new HttpRequestMessage(HttpMethod.Post, url)
        {
            Content = new StringContent(JsonSerializer.Serialize(requestBody, _serializerOptions), Encoding.UTF8, "application/json")
        };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

        var response = await client.SendAsync(request, cancellationToken).ConfigureAwait(false);
        if (!response.IsSuccessStatusCode)
        {
            var error = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            _logger.LogWarning("FCM notification failed: {Status} {Body}", response.StatusCode, error);
        }
    }

    private static string ResolveAccountId(FirebaseConfig config)
    {
        return Environment.GetEnvironmentVariable("BIOME_ACCOUNT_ID") ?? config.Web.ProjectId;
    }

    private static string ResolveDeviceId()
    {
        return Environment.GetEnvironmentVariable("BIOME_DEVICE_ID") ?? Environment.MachineName;
    }

    private string? ResolveFcmToken()
    {
        return Environment.GetEnvironmentVariable("BIOME_FCM_DEVICE_TOKEN") ?? _settings.Firebase.DeviceToken;
    }

    private string ResolveServiceAccountPath()
    {
        if (!string.IsNullOrWhiteSpace(_settings.Firebase.ServiceAccountPath))
        {
            return _settings.Firebase.ServiceAccountPath;
        }

        var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        if (string.IsNullOrWhiteSpace(home))
        {
            home = AppContext.BaseDirectory;
        }

        return Path.Combine(home, ".biome", "firebase.json");
    }

    private static string ResolveOutboxDirectory()
    {
        var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        if (string.IsNullOrWhiteSpace(home))
        {
            home = AppContext.BaseDirectory;
        }

        return Path.Combine(home, ".biome", "outbox");
    }

    public void Dispose()
    {
        _configLock.Dispose();
    }

    private sealed record OutboxEnvelope(
        string EnvelopeId,
        string PayloadId,
        string Reason,
        DateTimeOffset TimestampUtc,
        ClipboardPayload Payload,
        IReadOnlyDictionary<string, object?>? Context);

    private readonly record struct StorageEnvelope(
        [property: JsonPropertyName("kind")] string Kind,
        [property: JsonPropertyName("data")] string Data,
        [property: JsonPropertyName("metadata")] string Metadata,
        [property: JsonPropertyName("version")] int Version,
        [property: JsonPropertyName("sent_at")] long SentAtSeconds);

    private readonly record struct StorageUploadResult
    {
        [JsonPropertyName("generation")]
        public string? Generation { get; init; }
    }

    private sealed record FirestoreDocumentRequest
    {
        [JsonPropertyName("fields")]
        public Dictionary<string, FirestoreValue> Fields { get; init; } = new();
    }

    private sealed record FirestoreValue
    {
        [JsonPropertyName("stringValue")]
        public string? StringValue { get; init; }

        [JsonPropertyName("timestampValue")]
        public string? TimestampValue { get; init; }

        public static FirestoreValue String(string value) => new() { StringValue = value };

        public static FirestoreValue Timestamp(DateTimeOffset instant) => new()
        {
            TimestampValue = instant.ToUniversalTime().ToString("O").Replace("+00:00", "Z")
        };
    }

    private sealed record FcmRequest
    {
        [JsonPropertyName("message")]
        public FcmMessage Message { get; init; } = new();
    }

    private sealed record FcmMessage
    {
        [JsonPropertyName("token")]
        public string Token { get; init; } = string.Empty;

        [JsonPropertyName("data")]
        public Dictionary<string, string> Data { get; init; } = new();
    }
}
