namespace IntegrationTracking.Api.Models;

public sealed class MessageEnvelope<T>
{
    public int Version { get; init; } = 1;
    public string MessageId { get; init; } = Guid.NewGuid().ToString("N");
    public string CorrelationId { get; init; } = string.Empty;
    public DateTime OccurredAtUtc { get; init; } = DateTime.UtcNow;
    public T Payload { get; init; } = default!;
}

public sealed class AnalysisFailedPayload
{
    public string EmailId { get; init; } = string.Empty;
    public string Error { get; init; } = string.Empty;
    public int Attempts { get; init; }
}
