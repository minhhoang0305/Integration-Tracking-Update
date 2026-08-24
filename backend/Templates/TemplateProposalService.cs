using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Templates;

public sealed class TemplateProposalService(
    IntegrationTrackingDbContext database, IIntegrationStorage storage, InstalledIntegrationCatalog catalog, ManifestDiffService diffService,
    ImpactAnalysisService impactService, RabbitMqPublisher publisher, IOptions<TemplateOptions> options,
    ILogger<TemplateProposalService> logger)
{
    private readonly TemplateOptions _options = options.Value;
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };

    public async Task GenerateAsync(EmailAnalysis analysis, ChangeSignal signal, CancellationToken ct)
    {
        if (!signal.ChangeDetected) return;
        var resolution = catalog.Resolve(analysis, signal);
        if (resolution.Status != "Resolved" || resolution.Integration is null) { await SaveUnresolvedAsync(analysis, resolution, ct); return; }

        var integration = resolution.Integration;
        if (await database.TemplateProposals.AnyAsync(x => x.EmailId == analysis.EmailId && x.IntegrationId == integration.IntegrationId, ct)) return;
        var proposal = new TemplateProposal { EmailId = analysis.EmailId, Provider = integration.Provider, IntegrationId = integration.IntegrationId };
        database.TemplateProposals.Add(proposal);
        try
        {
            if (signal.DeprecatedEndpoints.Count == 0 && signal.AnnouncedEndpoints.Count == 0)
                throw new InvalidOperationException("Email endpoint patch mode requires at least one deprecated or announced endpoint.");
            var current = catalog.ReadManifest(integration.IntegrationId);
            using var currentJson = JsonDocument.Parse(current);
            ManifestDiffService.ValidateManifest(currentJson.RootElement);
            proposal.BaseManifestHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(current)));
            var proposed = CreatePatch(current, signal);
            var diff = diffService.Compare(current, proposed);
            var impact = impactService.Analyze(integration.Provider, integration.IntegrationId, diff, signal);
            var relative = $"proposals/{proposal.Id}";
            var evidence = new { source = "email_endpoint_patch", label = "Email-derived test proposal — unverified", resolution,
                signal.DeprecatedEndpoints, signal.AnnouncedEndpoints, warnings = signal.Evidence.ParserWarnings, diff, impact };
            await storage.WriteProposalTextAsync(proposal.Id, "actions_manifest.json", proposed, ct);
            await storage.WriteProposalTextAsync(proposal.Id, "CHANGELOG.md", Changelog(analysis, signal, diff, impact, integration), ct);
            await storage.WriteProposalTextAsync(proposal.Id, "diff.patch", ManifestDiffService.BuildUnifiedDiff(current, proposed), ct);
            await storage.WriteProposalTextAsync(proposal.Id, "evidence.json", JsonSerializer.Serialize(evidence, JsonOptions), ct);
            await storage.WriteProposalTextAsync(proposal.Id, "impact.json", JsonSerializer.Serialize(impact, JsonOptions), ct);
            proposal.ArtifactDirectory = relative; proposal.EvidenceJson = JsonSerializer.Serialize(evidence, JsonOptions);
            proposal.ImpactJson = JsonSerializer.Serialize(impact, JsonOptions); proposal.ImpactSeverity = impact.OverallSeverity;
            proposal.Status = ProposalStatuses.Pending; proposal.UpdatedAt = DateTime.UtcNow;
            await database.SaveChangesAsync(ct);
            await publisher.PublishAuditEventAsync(RabbitMqTopology.IntegrationProposalRoutingKey, proposal.Id,
                new { proposal.Id, proposal.EmailId, proposal.Provider, proposal.IntegrationId, proposal.Status }, ct);
        }
        catch (Exception exception)
        {
            proposal.Status = ProposalStatuses.NeedsReview; proposal.ErrorMessage = exception.Message; proposal.UpdatedAt = DateTime.UtcNow;
            await database.SaveChangesAsync(ct); logger.LogWarning(exception, "Proposal generation needs review for email {EmailId}", analysis.EmailId);
        }
    }

    private async Task SaveUnresolvedAsync(EmailAnalysis analysis, IntegrationResolution resolution, CancellationToken ct)
    {
        if (await database.TemplateProposals.AnyAsync(x => x.EmailId == analysis.EmailId && x.IntegrationId == "unmapped", ct)) return;
        database.TemplateProposals.Add(new TemplateProposal { EmailId = analysis.EmailId, Provider = resolution.Status == "Ambiguous" ? "ambiguous" : "unknown",
            IntegrationId = "unmapped", Status = ProposalStatuses.NeedsReview, ErrorMessage = resolution.Reason,
            EvidenceJson = JsonSerializer.Serialize(new { source = "resolution", resolution }, JsonOptions) });
        await database.SaveChangesAsync(ct);
    }

    private static string CreatePatch(string current, ChangeSignal signal)
    {
        var root = JsonNode.Parse(current)?.AsObject() ?? throw new InvalidOperationException("Current manifest is invalid JSON.");
        var actions = root["actions"]?.AsArray() ?? throw new InvalidOperationException("Current manifest has no actions array.");
        var deprecated = Keys(signal.DeprecatedEndpoints);
        for (var index = actions.Count - 1; index >= 0; index--)
            if (actions[index] is JsonObject action && deprecated.Contains(Key(action["http_method"]?.GetValue<string>() ?? "", action["endpoint"]?.GetValue<string>() ?? ""))) actions.RemoveAt(index);
        var existing = actions.OfType<JsonObject>().Select(action => Key(action["http_method"]?.GetValue<string>() ?? "", action["endpoint"]?.GetValue<string>() ?? "")).ToHashSet(StringComparer.OrdinalIgnoreCase);
        foreach (var endpoint in signal.AnnouncedEndpoints.Where(x => !deprecated.Contains(Key(x.Method, x.Path))))
        {
            var key = Key(endpoint.Method, endpoint.Path); if (existing.Contains(key)) continue;
            actions.Add(new JsonObject { ["name"] = Name(endpoint.Method, endpoint.Path), ["description"] = "Email-derived test action. Verify request and response schema before applying.",
                ["http_method"] = endpoint.Method.ToUpperInvariant(), ["endpoint"] = endpoint.Path,
                ["input_schema"] = new JsonObject { ["type"] = "object", ["properties"] = new JsonObject() } });
            existing.Add(key);
        }
        return root.ToJsonString(JsonOptions);
    }

    private static HashSet<string> Keys(IEnumerable<ApiEndpoint> values) => values.Select(x => Key(x.Method, x.Path)).ToHashSet(StringComparer.OrdinalIgnoreCase);
    private static string Key(string method, string path) => method.ToUpperInvariant() + " " + path;
    private static string Name(string method, string path) => (method + "_" + path.Trim('/').Replace("{", "").Replace("}", "")).ToLowerInvariant().Replace('/', '_').Replace('-', '_').Replace('.', '_').Replace("__", "_");
    private static string Changelog(EmailAnalysis email, ChangeSignal signal, ManifestDiff diff, IntegrationImpactAnalysis impact, InstalledIntegration integration) =>
        $"# Email-derived test proposal\n\nProvider notification: **{email.Subject}**\n\n## Source\n\n- Integration folder: `{integration.Folder}`\n- Mode: email endpoint patch (unverified)\n\n## Endpoint changes from email\n\n- Deprecated: {signal.DeprecatedEndpoints.Count}\n- Announced: {signal.AnnouncedEndpoints.Count}\n\n## Manifest diff\n\n- Removed: {diff.RemovedActions.Count}\n- Added: {diff.AddedActions.Count}\n- Changed: {diff.ChangedActions.Count}\n\n## Impact\n\n- Overall severity: **{impact.OverallSeverity}**\n";
}
