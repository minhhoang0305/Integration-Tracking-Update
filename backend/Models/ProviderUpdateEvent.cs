namespace IntegrationTracking.Api.Models;

public sealed class ProviderUpdateEvent
{
    // Stable event ID lets downstream services handle redelivery idempotently.
    public string EventId { get; init; } = string.Empty;
    public string EmailId { get; init; } = string.Empty;
    public string Provider { get; init; } = string.Empty;
    public ProviderEmailSource Source { get; init; } = new();
    public List<string> ChangeTypes { get; init; } = [];
    public string? Summary { get; init; }
    public double Confidence { get; init; }
    public ChangeEvidence Evidence { get; init; } = new();
    public DateTime DetectedAt { get; init; } = DateTime.UtcNow;
}

public sealed class ProviderEmailSource
{
    public string Sender { get; init; } = string.Empty;
    public string Subject { get; init; } = string.Empty;
    public DateTime ReceivedAt { get; init; }
}
