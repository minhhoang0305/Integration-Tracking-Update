using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Templates;

public sealed class TemplateProposalService(
    IntegrationTrackingDbContext database, TemplateRegistryService registry, DocumentationEvidenceService documentation,
    ProposalLlmClient llm, ManifestDiffService diffService, ImpactAnalysisService impactService, RabbitMqPublisher publisher, IOptions<TemplateOptions> options, ILogger<TemplateProposalService> logger)
{
    private readonly TemplateOptions _options = options.Value;
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };

    public async Task GenerateAsync(EmailAnalysis analysis, ChangeSignal signal, CancellationToken cancellationToken)
    {
        if (!signal.ChangeDetected) return;
        var provider = registry.FindProvider(analysis.Sender);
        if (provider is null)
        {
            await SaveUnmappedAsync(analysis, "Provider is not present in provider registry.", cancellationToken);
            return;
        }
        if (provider.Integrations.Count != 1)
        {
            await SaveUnmappedAsync(analysis, "Provider maps to zero or multiple integrations; manual selection is required.", cancellationToken, provider.Provider);
            return;
        }
        var integration = provider.Integrations[0];
        if (await database.TemplateProposals.AnyAsync(x => x.EmailId == analysis.EmailId && x.IntegrationId == integration.Id, cancellationToken)) return;
        var proposal = new TemplateProposal { EmailId = analysis.EmailId, Provider = provider.Provider, IntegrationId = integration.Id };
        database.TemplateProposals.Add(proposal);
        try
        {
            var manifestPath = registry.WorkspacePath(integration.ManifestPath);
            if (!File.Exists(manifestPath)) throw new InvalidOperationException("Registered actions_manifest.json was not found.");
            var current = await File.ReadAllTextAsync(manifestPath, cancellationToken);
            using var currentJson = JsonDocument.Parse(current);
            ManifestDiffService.ValidateManifest(currentJson.RootElement);
            proposal.BaseManifestHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(current)));

            string proposedJson;
            string changelog;
            string risk;
            object evidence;
            IntegrationImpactAnalysis? impact = null;
            if (integration.ProposalMode.Equals("verified_snapshot", StringComparison.OrdinalIgnoreCase))
            {
                if (string.IsNullOrWhiteSpace(integration.VerifiedManifestPath)) throw new InvalidOperationException("verified_snapshot mode requires verifiedManifestPath.");
                var verifiedPath = registry.WorkspacePath(integration.VerifiedManifestPath);
                if (!File.Exists(verifiedPath)) throw new InvalidOperationException("Verified manifest snapshot was not found.");
                proposedJson = await File.ReadAllTextAsync(verifiedPath, cancellationToken);
                var diff = diffService.Compare(current, proposedJson);
                impact = impactService.Analyze(provider.Provider, integration.Id, diff, signal);
                changelog = BuildVerifiedSnapshotChangelog(analysis, signal, diff, impact);
                risk = "High: this proposal removes legacy endpoints and replaces the integration action set.";
                evidence = new
                {
                    source = "verified_snapshot",
                    snapshotPath = integration.VerifiedManifestPath,
                    signal.DeprecatedEndpoints,
                    signal.AnnouncedEndpoints,
                    diff,
                    impact
                };
            }
            else
            {
                var documentationEvidence = await documentation.ReadAsync(signal.DocumentationUrls.Concat(signal.Evidence.Urls), provider.DocumentationDomains, cancellationToken);
                if (documentationEvidence.Count == 0) throw new InvalidOperationException("No allow-listed documentation evidence was available.");
                var generated = await llm.GenerateAsync(provider.Provider, integration.Id, current, documentationEvidence, cancellationToken);
                ManifestDiffService.ValidateManifest(generated.Manifest);
                proposedJson = JsonSerializer.Serialize(generated.Manifest, JsonOptions);
                changelog = BuildLlmChangelog(analysis, signal, generated);
                risk = generated.Risk;
                evidence = new { source = "llm", urls = signal.DocumentationUrls, documentationEvidence, generated.Risk };
            }

            var relativeDirectory = Path.Combine(_options.ArtifactRoot, proposal.Id).Replace('\\', '/');
            var directory = registry.ContentPath(relativeDirectory);
            Directory.CreateDirectory(directory);
            await File.WriteAllTextAsync(Path.Combine(directory, "actions_manifest.json"), proposedJson, cancellationToken);
            await File.WriteAllTextAsync(Path.Combine(directory, "CHANGELOG.md"), changelog, cancellationToken);
            await File.WriteAllTextAsync(Path.Combine(directory, "diff.patch"), ManifestDiffService.BuildUnifiedDiff(current, proposedJson), cancellationToken);
            await File.WriteAllTextAsync(Path.Combine(directory, "evidence.json"), JsonSerializer.Serialize(evidence, JsonOptions), cancellationToken);
            if (impact is not null)
                await File.WriteAllTextAsync(Path.Combine(directory, "impact.json"), JsonSerializer.Serialize(impact, JsonOptions), cancellationToken);
            proposal.ArtifactDirectory = relativeDirectory;
            proposal.EvidenceJson = JsonSerializer.Serialize(evidence, JsonOptions);
            proposal.ImpactJson = impact is null ? "{}" : JsonSerializer.Serialize(impact, JsonOptions);
            proposal.ImpactSeverity = impact?.OverallSeverity ?? "Unknown";
            proposal.Status = ProposalStatuses.Pending;
            proposal.UpdatedAt = DateTime.UtcNow;
            await database.SaveChangesAsync(cancellationToken);
            await publisher.PublishAuditEventAsync(RabbitMqTopology.IntegrationProposalRoutingKey, proposal.Id, new { proposal.Id, proposal.EmailId, proposal.Provider, proposal.IntegrationId, proposal.Status }, cancellationToken);
        }
        catch (Exception exception)
        {
            proposal.Status = ProposalStatuses.NeedsReview;
            proposal.ErrorMessage = exception.Message;
            proposal.UpdatedAt = DateTime.UtcNow;
            await database.SaveChangesAsync(cancellationToken);
            logger.LogWarning(exception, "Proposal generation needs review for email {EmailId}", analysis.EmailId);
        }
    }

    private async Task SaveUnmappedAsync(EmailAnalysis analysis, string reason, CancellationToken ct, string provider = "unknown")
    {
        if (await database.TemplateProposals.AnyAsync(x => x.EmailId == analysis.EmailId && x.IntegrationId == "unmapped", ct)) return;
        database.TemplateProposals.Add(new TemplateProposal { EmailId = analysis.EmailId, Provider = provider, IntegrationId = "unmapped", Status = ProposalStatuses.NeedsReview, ErrorMessage = reason });
        await database.SaveChangesAsync(ct);
    }
    private static string BuildLlmChangelog(EmailAnalysis analysis, ChangeSignal signal, LlmProposal proposal) => $"# Proposed change\n\nProvider notification: **{analysis.Subject}**\n\n## Summary\n\n{signal.Summary}\n\n## Generated change notes\n\n{proposal.Changelog}\n\n## Risk\n\n{proposal.Risk}\n";
    private static string BuildVerifiedSnapshotChangelog(EmailAnalysis analysis, ChangeSignal signal, ManifestDiff diff, IntegrationImpactAnalysis impact) => $"# Verified snapshot proposal\n\nProvider notification: **{analysis.Subject}**\n\n## Summary\n\n{signal.Summary}\n\n## Action changes\n\n- Removed: {diff.RemovedActions.Count}\n- Added: {diff.AddedActions.Count}\n- Changed: {diff.ChangedActions.Count}\n- Top-level configuration changes: {(diff.TopLevelChanges.Count == 0 ? "none" : string.Join(", ", diff.TopLevelChanges))}\n\n## Impact\n\n- Overall severity: **{impact.OverallSeverity}**\n- Affected existing actions: {impact.AffectedActions.Count}\n- New actions: {impact.NewActions.Count}\n\n## Risk\n\nHigh: legacy actions are removed. Review and apply through Git only after approval.\n";
}
