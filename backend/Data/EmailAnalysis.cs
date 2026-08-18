namespace IntegrationTracking.Api.Data;

public sealed class EmailAnalysis
{
    public string EmailId { get; set; } = string.Empty;
    public string Sender { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string Body { get; set; } = string.Empty;
    public DateTime ReceivedAt { get; set; }
    public string Status { get; set; } = AnalysisStatuses.Queued;
    public string? ResultJson { get; set; }
    public string? ErrorMessage { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public static class AnalysisStatuses
{
    public const string Queued = "Queued";
    public const string Completed = "Completed";
    public const string Failed = "Failed";
}
