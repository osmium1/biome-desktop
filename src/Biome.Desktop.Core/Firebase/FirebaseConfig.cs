using System.Text.Json.Serialization;

namespace Biome.Desktop.Core.Firebase;

/// <summary>
/// Represents the combined firebase.json data (web config + service account credentials).
/// </summary>
public sealed class FirebaseConfig
{
    [JsonPropertyName("web")]
    public WebConfig Web { get; init; } = new();

    [JsonPropertyName("serviceAccount")]
    public ServiceAccountConfig ServiceAccount { get; init; } = new();

    public sealed class WebConfig
    {
        [JsonPropertyName("apiKey")]
        public string ApiKey { get; init; } = string.Empty;

        [JsonPropertyName("authDomain")]
        public string AuthDomain { get; init; } = string.Empty;

        [JsonPropertyName("projectId")]
        public string ProjectId { get; init; } = string.Empty;

        [JsonPropertyName("storageBucket")]
        public string StorageBucket { get; init; } = string.Empty;

        [JsonPropertyName("messagingSenderId")]
        public string MessagingSenderId { get; init; } = string.Empty;

        [JsonPropertyName("appId")]
        public string AppId { get; init; } = string.Empty;
    }

    public sealed class ServiceAccountConfig
    {
        [JsonPropertyName("project_id")]
        public string ProjectId { get; init; } = string.Empty;

        [JsonPropertyName("private_key_id")]
        public string PrivateKeyId { get; init; } = string.Empty;

        [JsonPropertyName("private_key")]
        public string PrivateKey { get; init; } = string.Empty;

        [JsonPropertyName("client_email")]
        public string ClientEmail { get; init; } = string.Empty;

        [JsonPropertyName("client_id")]
        public string ClientId { get; init; } = string.Empty;

        [JsonPropertyName("token_uri")]
        public string TokenUri { get; init; } = "https://oauth2.googleapis.com/token";
    }
}
