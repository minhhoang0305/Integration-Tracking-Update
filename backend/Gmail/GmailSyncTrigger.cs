using System.Threading.Channels;

namespace IntegrationTracking.Api.Gmail;

public sealed class GmailSyncTrigger
{
    private readonly Channel<bool> _signals = Channel.CreateBounded<bool>(1);
    public void Trigger() => _signals.Writer.TryWrite(true);
    public async Task WaitAsync(TimeSpan fallback, CancellationToken cancellationToken)
    {
        await Task.WhenAny(_signals.Reader.ReadAsync(cancellationToken).AsTask(), Task.Delay(fallback, cancellationToken));
        while (_signals.Reader.TryRead(out _)) { }
    }
}
