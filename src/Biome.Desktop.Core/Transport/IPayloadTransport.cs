using System.Threading;
using System.Threading.Tasks;
using Biome.Desktop.Core.Payloads;

namespace Biome.Desktop.Core.Transport;

public interface IPayloadTransport
{
    Task SendAsync(ClipboardPayload payload, CancellationToken cancellationToken);
}
