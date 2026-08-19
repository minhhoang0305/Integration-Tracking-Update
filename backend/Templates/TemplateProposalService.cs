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
    ProposalLlmClient llm, RabbitMqPublisher publisher, IOptions<TemplateOptions> options, ILogger<TemplateProposalService> logger)
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
            var manifestPath = registry.AbsolutePath(integration.ManifestPath);
            if (!File.Exists(manifestPath)) throw new InvalidOperationException("Registered actions_manifest.json was not found.");
            var current = await File.ReadAllTextAsync(manifestPath, cancellationToken);
            using var currentJson = JsonDocument.Parse(current);
            ValidateManifest(currentJson.RootElement);
            proposal.BaseManifestHash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(current)));
            var evidence = await documentation.ReadAsync(signal.DocumentationUrls.Concat(signal.Evidence.Urls), provider.DocumentationDomains, cancellationToken);
            if (evidence.Count == 0) throw new InvalidOperationException("No allow-listed documentation evidence was available.");
            var generated = await llm.GenerateAsync(provider.Provider, integration.Id, current, evidence, cancellationToken);
            ValidateManifest(generated.Manifest);
            var relativeDirectory = Path.Combine(_options.ArtifactRoot, proposal.Id).Replace('\\', '/');
            var directory = registry.AbsolutePath(relativeDirectory);
            Directory.CreateDirectory(directory);
            var proposedJson = JsonSerializer.Serialize(generated.Manifest, JsonOptions);
            await File.WriteAllTextAsync(Path.Combine(directory, "actions_manifest.json"), proposedJson, cancellationToken);
            await File.WriteAllTextAsync(Path.Combine(directory, "CHANGELOG.md"), BuildChangelog(analysis, signal, generated), cancellationToken);
            await File.WriteAllTextAsync(Path.Combine(directory, "diff.patch"), BuildUnifiedDiff(current, proposedJson), cancellationToken);
            await File.WriteAllTextAsync(Path.Combine(directory, "evidence.json"), JsonSerializer.Serialize(new { urls = signal.DocumentationUrls, evidence, risk = generated.Risk }, JsonOptions), cancellationToken);
            proposal.ArtifactDirectory = relativeDirectory;
            proposal.EvidenceJson = JsonSerializer.Serialize(new { signal.DocumentationUrls, signal.Evidence, generated.Risk }, JsonOptions);
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
    private static void ValidateManifest(JsonElement manifest)
    {
        if (manifest.ValueKind != JsonValueKind.Object || !manifest.TryGetProperty("actions", out var actions) || actions.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("Proposed actions_manifest.json must be an object containing an actions array.");
    }
    private static string BuildChangelog(EmailAnalysis analysis, ChangeSignal signal, LlmProposal proposal) => $"# Proposed change\n\nProvider notification: **{analysis.Subject}**\n\n## Summary\n\n{signal.Summary}\n\n## Generated change notes\n\n{proposal.Changelog}\n\n## Risk\n\n{proposal.Risk}\n";
    private static string BuildUnifiedDiff(string current, string proposed) => $"--- a/actions_manifest.json\n+++ b/actions_manifest.json\n@@ -1,{current.Split('\n').Length} +1,{proposed.Split('\n').Length} @@\n" + string.Join('\n', current.Split('\n').Select(x => "-" + x)) + "\n" + string.Join('\n', proposed.Split('\n').Select(x => "+" + x)) + "\n";
}
