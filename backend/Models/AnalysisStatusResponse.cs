namespace IntegrationTracking.Api.Models;

public sealed class AnalysisStatusResponse
{
    public string EmailId { get; init; } = string.Empty;
    public string Status { get; init; } = string.Empty;
    public ChangeSignal? Result { get; init; }
    public string? Error { get; init; }
    public DateTime CreatedAt { get; init; }
    public DateTime UpdatedAt { get; init; }
}
