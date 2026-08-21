namespace IntegrationTracking.Api.Data;

public sealed class TemplateProposal
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string EmailId { get; set; } = string.Empty;
    public string Provider { get; set; } = string.Empty;
    public string IntegrationId { get; set; } = string.Empty;
    public string BaseManifestHash { get; set; } = string.Empty;
    public string Status { get; set; } = ProposalStatuses.Pending;
    public string? ErrorMessage { get; set; }
    public string ArtifactDirectory { get; set; } = string.Empty;
    public string EvidenceJson { get; set; } = "{}";
    public string ImpactJson { get; set; } = "{}";
    public string ImpactSeverity { get; set; } = "Unknown";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}

public sealed class ReviewDecision
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string ProposalId { get; set; } = string.Empty;
    public string Decision { get; set; } = string.Empty;
    public string AdminIdentity { get; set; } = string.Empty;
    public string? Note { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public static class ProposalStatuses
{
    public const string Pending = "Pending";
    public const string NeedsReview = "NeedsReview";
    public const string Approved = "Approved";
    public const string Rejected = "Rejected";
    public const string Failed = "Failed";
}
