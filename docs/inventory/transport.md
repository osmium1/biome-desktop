# Transport + Firebase Integration

The current transport is still a staging placeholder that writes envelopes to `%USERPROFILE%/.biome/outbox` if anything goes wrong. This document captures its flow and open gaps.

## `FirebasePayloadTransport`
Registered as the `IPayloadTransport` implementation, this class performs several steps before attempting to hit Google APIs.

```csharp
public async Task SendAsync(ClipboardPayload payload, CancellationToken cancellationToken)
{
    if (!TryBuildTransportContent(payload, out var envelope, out var reason))
    {
        await WriteOutboxEnvelopeAsync(payload, reason, null, cancellationToken);
        return;
    }

    var configPath = ResolveServiceAccountPath();
    if (!File.Exists(configPath))
    {
        await WriteOutboxEnvelopeAsync(payload, "service-account-file-not-found", ...);
        return;
    }

    var config = await GetFirebaseConfigAsync(configPath, cancellationToken);
    var validationErrors = FirebaseConfigLoader.Validate(config);
    var token = await _tokenProvider.GetAccessTokenAsync(config!, cancellationToken);

    var accountId = ResolveAccountId(config!);
    var storagePath = $"clips/{accountId}/{clipId}.json";
    var httpClient = _httpClientFactory.CreateClient("FirebaseTransport");

    try
    {
        var uploadResult = await UploadPayloadAsync(...);
        await CreateFirestoreDocumentAsync(...);
        await SendFcmNotificationAsync(...);
    }
    catch (Exception ex)
    {
        await WriteOutboxEnvelopeAsync(payload, "firebase-send-error", new { storagePath, exception = ex.Message }, cancellationToken);
    }
}
```

Important helpers:
- `TryBuildTransportContent` converts payloads into JSON `StorageEnvelope` objects (text stays plain string; images become base64-encoded PNG blobs) and attaches metadata such as capture timestamp and machine name.
- `WriteOutboxEnvelopeAsync` records failures so support can inspect them later. Files are indented JSON with fields `envelopeId`, `payload`, `reason`, and optional context dictionary.
- `ResolveServiceAccountPath` respects `Biome.Firebase.ServiceAccountPath` from settings but falls back to `%USERPROFILE%/.biome/firebase.json`.

### Idle pieces / TODOs
- The HTTP clients named `"FirebaseTransport"` and `"FirebaseOAuth"` are created via `AddHttpClient()` but not further configured (no retry policy, timeout, etc.).
- No encryption-at-rest for the outbox; files may contain raw clipboard text or base64 images.
- `ResolveAccountId` currently mirrors `BIOME_ACCOUNT_ID` env var or `config.Web.ProjectId`; it does not read any per-user identity yet.

## `FirebaseTokenProvider`
Handles JWT assertion + OAuth token exchange and caches tokens until one minute before expiration.

```csharp
public async Task<FirebaseAccessToken?> GetAccessTokenAsync(FirebaseConfig config, CancellationToken cancellationToken)
{
    if (_cachedToken is { } cached && cached.ExpiresAtUtc > DateTimeOffset.UtcNow.AddMinutes(1))
    {
        return cached;
    }

    await _tokenSemaphore.WaitAsync(cancellationToken);
    try
    {
        var assertion = CreateAssertion(config);
        var tokenResponse = await RequestTokenAsync(assertion, config.ServiceAccount.TokenUri, cancellationToken);
        _cachedToken = new FirebaseAccessToken(tokenResponse.AccessToken, expiresAt);
        return _cachedToken;
    }
    finally
    {
        _tokenSemaphore.Release();
    }
}
```

`CreateAssertion` signs the JWT using the PEM private key from the service account section in the combined `firebase.json`. Request failures log an error and return null, causing the payload to be dropped into the outbox with reason `firebase-token-unavailable`.
