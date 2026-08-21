namespace IntegrationTracking.Api.Models;

public sealed class ChangeSignal
{
    public string EmailId { get; set; } = string.Empty;

    public string? Provider { get; set; }

    public bool IsApiRelated { get; set; }

    public bool ChangeDetected { get; set; }

    public List<string> ChangeTypes { get; set; } = [];

    public string? Summary { get; set; }

    public List<string> AffectedEndpoints { get; set; } = [];

    public List<ApiEndpoint> DeprecatedEndpoints { get; set; } = [];

    public List<ApiEndpoint> AnnouncedEndpoints { get; set; } = [];

    public bool BreakingChange { get; set; }

    public bool MigrationRequired { get; set; }

    public DateTime? EffectiveDate { get; set; }

    public List<string> DocumentationUrls { get; set; } = [];

    public double Confidence { get; set; }

    public ChangeEvidence Evidence { get; set; } = new();
}

public sealed class ApiEndpoint
{
    public string Method { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
}

public sealed class ChangeEvidence
{
    public List<string> MatchedTerms { get; set; } = [];
    public List<string> Urls { get; set; } = [];
}
