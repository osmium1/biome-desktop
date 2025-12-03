using System.Threading;
using System.Threading.Tasks;
using Biome.Desktop.Core.Payloads;

namespace Biome.Desktop.Core.Clipboard;

public interface IClipboardService
{
    Task<ClipboardPayload?> CaptureAsync(CancellationToken cancellationToken);
}
