using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Services;
using IntegrationTracking.Api.Templates;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace IntegrationTracking.Api.Controllers;

[ApiController]
[Route("api/reviews")]
public sealed class ReviewsController(IntegrationTrackingDbContext database, IIntegrationStorage storage, InstalledIntegrationCatalog catalog, RabbitMqPublisher publisher) : ControllerBase
{
    [HttpGet]
    public async Task<List<ReviewListItem>> List(CancellationToken ct)
    {
        var proposals = await database.TemplateProposals.OrderByDescending(x => x.CreatedAt).ToListAsync(ct);
        return proposals.Select(proposal =>
        {
            var impact = ParseJson(proposal.ImpactJson);
            return new ReviewListItem(
                ProposalMetadata.From(proposal),
                impact?["affectedActions"]?.AsArray().Count ?? 0,
                impact?["newActions"]?.AsArray().Count ?? 0);
        }).ToList();
    }

    [HttpGet("{id}")]
    public async Task<IActionResult> Get(string id, CancellationToken ct)
    {
        var proposal = await database.TemplateProposals.FindAsync([id], ct);
        if (proposal is null) return NotFound();
        var integration = catalog.Find(proposal.Provider, proposal.IntegrationId);
        var original = integration is null ? null : ParseJson(catalog.ReadManifest(integration.IntegrationId));
        return Ok(new
        {
            proposal = ProposalMetadata.From(proposal),
            evidence = ParseJson(proposal.EvidenceJson),
            impact = ParseJson(proposal.ImpactJson),
            originalManifest = original,
            artifacts = (string.IsNullOrWhiteSpace(proposal.ArtifactDirectory) ? null : new
            {
                proposedManifest = ParseJson(storage.ReadProposalText(proposal.Id, "actions_manifest.json")),
                changelog = storage.ReadProposalText(proposal.Id, "CHANGELOG.md"),
                diff = storage.ReadProposalText(proposal.Id, "diff.patch"),
                diffModel = ParseJson(storage.ReadProposalText(proposal.Id, "diff.json")),
                evidence = ParseJson(storage.ReadProposalText(proposal.Id, "evidence.json")),
                impact = ParseJson(storage.ReadProposalText(proposal.Id, "impact.json"))
            })
        });
    }

    [HttpPost("{id}/approve")]
    public Task<IActionResult> Approve(string id, [FromBody] ReviewRequest request, CancellationToken ct) => Decide(id, ProposalStatuses.Approved, request, ct);
    [HttpPost("{id}/reject")]
    public Task<IActionResult> Reject(string id, [FromBody] ReviewRequest request, CancellationToken ct) => Decide(id, ProposalStatuses.Rejected, request, ct);
    [HttpPost("{id}/regenerate")]
    public async Task<IActionResult> Regenerate(string id, [FromBody] ReviewRequest request, CancellationToken ct)
    {
        var proposal = await database.TemplateProposals.FindAsync([id], ct); if (proposal is null) return NotFound();
        proposal.Status = ProposalStatuses.NeedsReview; proposal.ErrorMessage = "Regeneration requested: " + request.Note; proposal.UpdatedAt = DateTime.UtcNow;
        database.ReviewDecisions.Add(new ReviewDecision { ProposalId = id, Decision = "Regenerate", AdminIdentity = request.AdminIdentity, Note = request.Note });
        await database.SaveChangesAsync(ct); return Accepted(new { proposal.Id, proposal.Status });
    }
    private async Task<IActionResult> Decide(string id, string decision, ReviewRequest request, CancellationToken ct)
    {
        var proposal = await database.TemplateProposals.FindAsync([id], ct); if (proposal is null) return NotFound();
        if (proposal.Status is not ProposalStatuses.Pending and not ProposalStatuses.NeedsReview) return Conflict(new { message = "Proposal has already been decided." });
        proposal.Status = decision; proposal.UpdatedAt = DateTime.UtcNow;
        database.ReviewDecisions.Add(new ReviewDecision { ProposalId = id, Decision = decision, AdminIdentity = request.AdminIdentity, Note = request.Note });
        await database.SaveChangesAsync(ct);
        await publisher.PublishAuditEventAsync(RabbitMqTopology.IntegrationReviewRoutingKey, id, new { proposal.Id, proposal.Status, request.AdminIdentity }, ct);
        return Ok(new { proposal.Id, proposal.Status });
    }
    private static JsonNode? ParseJson(string? json)
    {
        if (string.IsNullOrWhiteSpace(json)) return null;
        try
        {
            var node = JsonNode.Parse(json);
            NormalizeRawActions(node);
            return node;
        }
        catch (JsonException) { return null; }
    }

    private static void NormalizeRawActions(JsonNode? node)
    {
        switch (node)
        {
            case JsonObject obj:
                if (obj["rawJson"] is JsonValue raw && raw.TryGetValue<string>(out var rawJson))
                {
                    try { obj["definition"] = JsonNode.Parse(rawJson); obj.Remove("rawJson"); }
                    catch (JsonException) { /* Preserve the raw value when historical data is malformed. */ }
                }
                foreach (var child in obj.ToList()) NormalizeRawActions(child.Value);
                break;
            case JsonArray array:
                foreach (var child in array) NormalizeRawActions(child);
                break;
        }
    }
}

public sealed class ReviewRequest { public string AdminIdentity { get; set; } = string.Empty; public string? Note { get; set; } }
public sealed record ProposalMetadata(string Id, string EmailId, string Provider, string IntegrationId, string BaseManifestHash,
    string Status, string? ErrorMessage, string ArtifactDirectory, string ImpactSeverity, DateTime CreatedAt, DateTime UpdatedAt)
{
    public static ProposalMetadata From(TemplateProposal proposal) => new(proposal.Id, proposal.EmailId, proposal.Provider,
        proposal.IntegrationId, proposal.BaseManifestHash, proposal.Status, proposal.ErrorMessage, proposal.ArtifactDirectory,
        proposal.ImpactSeverity, proposal.CreatedAt, proposal.UpdatedAt);
}
public sealed record ReviewListItem(ProposalMetadata Proposal, int AffectedActionsCount, int NewActionsCount);
