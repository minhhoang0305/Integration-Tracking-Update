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

    public bool BreakingChange { get; set; }

    public bool MigrationRequired { get; set; }

    public DateTime? EffectiveDate { get; set; }

    public List<string> DocumentationUrls { get; set; } = [];

    public double Confidence { get; set; }
}