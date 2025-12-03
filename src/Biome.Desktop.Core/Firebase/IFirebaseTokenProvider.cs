using System;
using System.Threading;
using System.Threading.Tasks;

namespace Biome.Desktop.Core.Firebase;

public interface IFirebaseTokenProvider
{
    Task<FirebaseAccessToken?> GetAccessTokenAsync(FirebaseConfig config, CancellationToken cancellationToken);
}

public sealed record FirebaseAccessToken(string Token, DateTimeOffset ExpiresAtUtc);
