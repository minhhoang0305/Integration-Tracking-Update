using System.Text.Json;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace IntegrationTracking.Api.Services;

public sealed class EmailAnalysisService(
    IntegrationTrackingDbContext database,
    RabbitMqPublisher publisher)
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public async Task<AnalysisStatusResponse> QueueAsync(AnalyzeEmailRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.EmailId))
            throw new ArgumentException("EmailId is required.", nameof(request.EmailId));
        if (string.IsNullOrWhiteSpace(request.Sender))
            throw new ArgumentException("Sender is required.", nameof(request.Sender));
        if (string.IsNullOrWhiteSpace(request.Subject) && string.IsNullOrWhiteSpace(request.Body))
            throw new ArgumentException("Email subject or body is required.");

        var existing = await database.EmailAnalyses.FindAsync([request.EmailId], cancellationToken);
        if (existing is not null)
            return ToResponse(existing);

        var now = DateTime.UtcNow;
        var analysis = new EmailAnalysis
        {
            EmailId = request.EmailId, Sender = request.Sender, Subject = request.Subject,
            Body = request.Body, ReceivedAt = request.ReceivedAt, Status = AnalysisStatuses.Queued,
            CreatedAt = now, UpdatedAt = now
        };
        database.EmailAnalyses.Add(analysis);
        await database.SaveChangesAsync(cancellationToken);

        try
        {
            await publisher.PublishRequestedAsync(request, cancellationToken);
        }
        catch
        {
            analysis.Status = AnalysisStatuses.Failed;
            analysis.ErrorMessage = "Unable to publish analysis request.";
            analysis.UpdatedAt = DateTime.UtcNow;
            await database.SaveChangesAsync(cancellationToken);
            throw;
        }

        return ToResponse(analysis);
    }

    public async Task<AnalysisStatusResponse?> GetStatusAsync(string emailId, CancellationToken cancellationToken)
    {
        var analysis = await database.EmailAnalyses.FindAsync([emailId], cancellationToken);
        return analysis is null ? null : ToResponse(analysis);
    }

    public static AnalysisStatusResponse ToResponse(EmailAnalysis analysis) => new()
    {
        EmailId = analysis.EmailId, Status = analysis.Status, Error = analysis.ErrorMessage,
        Result = analysis.ResultJson is null ? null : JsonSerializer.Deserialize<ChangeSignal>(analysis.ResultJson, JsonOptions),
        CreatedAt = analysis.CreatedAt, UpdatedAt = analysis.UpdatedAt
    };
}
