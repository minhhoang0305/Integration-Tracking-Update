using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Services;
using IntegrationTracking.Api.Templates;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Text.Json;

namespace IntegrationTracking.Api.Controllers;

[ApiController]
[Route("api/reviews")]
public sealed class ReviewsController(IntegrationTrackingDbContext database, TemplateRegistryService registry, RabbitMqPublisher publisher) : ControllerBase
{
    [HttpGet]
    public Task<List<TemplateProposal>> List(CancellationToken ct) => database.TemplateProposals.OrderByDescending(x => x.CreatedAt).ToListAsync(ct);

    [HttpGet("{id}")]
    public async Task<IActionResult> Get(string id, CancellationToken ct)
    {
        var proposal = await database.TemplateProposals.FindAsync([id], ct);
        if (proposal is null) return NotFound();
        var directory = string.IsNullOrWhiteSpace(proposal.ArtifactDirectory) ? null : registry.ContentPath(proposal.ArtifactDirectory);
        var registration = registry.Load().Providers.FirstOrDefault(x => x.Provider.Equals(proposal.Provider, StringComparison.OrdinalIgnoreCase))?.Integrations.FirstOrDefault(x => x.Id == proposal.IntegrationId);
        var original = registration is null ? null : ReadAbsolute(registry.WorkspacePath(registration.ManifestPath));
        return Ok(new
        {
            proposal,
            impact = ParseJson(proposal.ImpactJson),
            originalManifest = original,
            artifacts = directory is not null && Directory.Exists(directory) ? new { manifest = Read(directory, "actions_manifest.json"), changelog = Read(directory, "CHANGELOG.md"), diff = Read(directory, "diff.patch"), evidence = Read(directory, "evidence.json"), impact = Read(directory, "impact.json") } : null
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
    private static string? Read(string directory, string name) { var path = Path.Combine(directory, name); return System.IO.File.Exists(path) ? System.IO.File.ReadAllText(path) : null; }
    private static string? ReadAbsolute(string path) => System.IO.File.Exists(path) ? System.IO.File.ReadAllText(path) : null;
    private static JsonElement? ParseJson(string json)
    {
        try { using var document = JsonDocument.Parse(json); return document.RootElement.Clone(); }
        catch (JsonException) { return null; }
    }
}

public sealed class ReviewRequest { public string AdminIdentity { get; set; } = string.Empty; public string? Note { get; set; } }
