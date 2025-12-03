using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Biome.Desktop.Core.Payloads;

namespace Biome.Desktop.Core.Dispatch;

public interface IPayloadDispatchQueue
{
    ValueTask EnqueueAsync(ClipboardPayload payload, CancellationToken cancellationToken);
    IAsyncEnumerable<ClipboardPayload> ReadAllAsync(CancellationToken cancellationToken);
}
