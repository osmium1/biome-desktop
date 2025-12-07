using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Biome.Desktop.Core.Dispatch;
using Biome.Desktop.Core.Payloads;

namespace Biome.Desktop.App.Dispatch;

public sealed class PayloadDispatchQueue : IPayloadDispatchQueue
{
    private readonly Channel<ClipboardPayload> _channel;

    public event EventHandler? PayloadEnqueued;

    public PayloadDispatchQueue()
    {
        var options = new UnboundedChannelOptions
        {
            AllowSynchronousContinuations = false,
            SingleReader = false,
            SingleWriter = false
        };
        _channel = Channel.CreateUnbounded<ClipboardPayload>(options);
    }

    public async ValueTask EnqueueAsync(ClipboardPayload payload, CancellationToken cancellationToken)
    {
        await _channel.Writer.WriteAsync(payload, cancellationToken);
        PayloadEnqueued?.Invoke(this, EventArgs.Empty);
    }

    public IAsyncEnumerable<ClipboardPayload> ReadAllAsync(CancellationToken cancellationToken)
        => _channel.Reader.ReadAllAsync(cancellationToken);
}
