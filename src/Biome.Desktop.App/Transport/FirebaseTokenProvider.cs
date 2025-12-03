using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Biome.Desktop.Core.Firebase;
using Microsoft.Extensions.Logging;
using System.Text.Json.Serialization;

namespace Biome.Desktop.App.Transport;

public sealed class FirebaseTokenProvider : IFirebaseTokenProvider, IDisposable
{
    private static readonly string[] Scopes =
    {
        "https://www.googleapis.com/auth/devstorage.read_write",
        "https://www.googleapis.com/auth/datastore",
        "https://www.googleapis.com/auth/firebase.messaging"
    };

    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<FirebaseTokenProvider> _logger;
    private readonly SemaphoreSlim _tokenSemaphore = new(1, 1);
    private FirebaseAccessToken? _cachedToken;

    public FirebaseTokenProvider(IHttpClientFactory httpClientFactory, ILogger<FirebaseTokenProvider> logger)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    public async Task<FirebaseAccessToken?> GetAccessTokenAsync(FirebaseConfig config, CancellationToken cancellationToken)
    {
        if (_cachedToken is { } cached && cached.ExpiresAtUtc > DateTimeOffset.UtcNow.AddMinutes(1))
        {
            return cached;
        }

        await _tokenSemaphore.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (_cachedToken is { } refreshed && refreshed.ExpiresAtUtc > DateTimeOffset.UtcNow.AddMinutes(1))
            {
                return refreshed;
            }

            var assertion = CreateAssertion(config);
            var tokenResponse = await RequestTokenAsync(assertion, config.ServiceAccount.TokenUri, cancellationToken).ConfigureAwait(false);
            if (tokenResponse is null)
            {
                return null;
            }

            var expiresAt = DateTimeOffset.UtcNow.AddSeconds(Math.Max(0, tokenResponse.ExpiresIn - 60));
            _cachedToken = new FirebaseAccessToken(tokenResponse.AccessToken, expiresAt);
            return _cachedToken;
        }
        finally
        {
            _tokenSemaphore.Release();
        }
    }

    private static string CreateAssertion(FirebaseConfig config)
    {
        var now = DateTimeOffset.UtcNow;
        var payload = new Dictionary<string, object>
        {
            ["iss"] = config.ServiceAccount.ClientEmail,
            ["scope"] = string.Join(' ', Scopes),
            ["aud"] = config.ServiceAccount.TokenUri,
            ["iat"] = now.ToUnixTimeSeconds(),
            ["exp"] = now.AddMinutes(55).ToUnixTimeSeconds()
        };

        var header = new Dictionary<string, object>
        {
            ["alg"] = "RS256",
            ["typ"] = "JWT"
        };

        var headerSegment = Base64UrlEncode(JsonSerializer.SerializeToUtf8Bytes(header));
        var payloadSegment = Base64UrlEncode(JsonSerializer.SerializeToUtf8Bytes(payload));
        var unsignedToken = Encoding.UTF8.GetBytes($"{headerSegment}.{payloadSegment}");

        using var rsa = RSA.Create();
        rsa.ImportFromPem(config.ServiceAccount.PrivateKey);
        var signature = rsa.SignData(unsignedToken, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
        var signatureSegment = Base64UrlEncode(signature);

        return $"{headerSegment}.{payloadSegment}.{signatureSegment}";
    }

    private async Task<TokenResponse?> RequestTokenAsync(string assertion, string tokenUri, CancellationToken cancellationToken)
    {
        var client = _httpClientFactory.CreateClient("FirebaseOAuth");
        var content = new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["grant_type"] = "urn:ietf:params:oauth:grant-type:jwt-bearer",
            ["assertion"] = assertion
        });
        content.Headers.ContentType = new MediaTypeHeaderValue("application/x-www-form-urlencoded");

        using var request = new HttpRequestMessage(HttpMethod.Post, tokenUri)
        {
            Content = content
        };

        try
        {
            var response = await client.SendAsync(request, cancellationToken).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();
            var stream = await response.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
            var tokenResponse = await JsonSerializer.DeserializeAsync<TokenResponse>(
                stream,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true },
                cancellationToken).ConfigureAwait(false);
            return tokenResponse;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to acquire Firebase OAuth token.");
            return null;
        }
    }

    private static string Base64UrlEncode(byte[] input)
    {
        return Convert.ToBase64String(input)
            .TrimEnd('=')
            .Replace('+', '-')
            .Replace('/', '_');
    }

    public void Dispose()
    {
        _tokenSemaphore.Dispose();
    }

    private sealed record TokenResponse
    {
        [JsonPropertyName("access_token")]
        public string AccessToken { get; init; } = string.Empty;

        [JsonPropertyName("expires_in")]
        public int ExpiresIn { get; init; }
    }
}
