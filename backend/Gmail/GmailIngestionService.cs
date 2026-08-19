using System.Security.Cryptography;
using System.Text;
using Google.Apis.Gmail.v1;
using Google.Apis.Gmail.v1.Data;
using Google.Apis.Services;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Gmail;

public sealed class GmailIngestionService(
    GmailOAuthService oauth,
    IntegrationTrackingDbContext database,
    ProviderEmailFilter filter,
    EmailNormalizer normalizer,
    EmailAnalysisService analyses,
    RabbitMqPublisher publisher,
    IOptions<GmailOptions> options,
    ILogger<GmailIngestionService> logger)
{
    private readonly GmailOptions _options = options.Value;
    public bool IsConfigured => _options.IsConfigured;

    public async Task SynchronizeAsync(CancellationToken cancellationToken)
    {
        if (!IsConfigured) return;
        var credential = await oauth.GetCredentialAsync(cancellationToken);
        using var gmail = new GmailService(new BaseClientService.Initializer { HttpClientInitializer = credential, ApplicationName = "Integration Tracking" });
        var profile = await gmail.Users.GetProfile("me").ExecuteAsync(cancellationToken);
        var state = await database.GmailSyncStates.FindAsync([_options.ServiceMailbox, "INBOX"], cancellationToken);
        if (state is null)
        {
            state = new GmailSyncState { Mailbox = _options.ServiceMailbox, Folder = "INBOX", HistoryId = profile.HistoryId?.ToString() ?? string.Empty };
            database.GmailSyncStates.Add(state);
            await EnsureWatchAsync(gmail, state, cancellationToken);
            await database.SaveChangesAsync(cancellationToken);
            return;
        }

        var messageIds = await GetChangedMessageIdsAsync(gmail, state.HistoryId, cancellationToken);
        foreach (var messageId in messageIds)
        {
            var message = await gmail.Users.Messages.Get("me", messageId).ExecuteAsync(cancellationToken);
            if (message.LabelIds?.Contains("INBOX") == true)
                await IngestAsync(message, cancellationToken);
        }
        state.HistoryId = profile.HistoryId?.ToString() ?? state.HistoryId;
        state.UpdatedAt = DateTime.UtcNow;
        await EnsureWatchAsync(gmail, state, cancellationToken);
        await database.SaveChangesAsync(cancellationToken);
    }

    private async Task EnsureWatchAsync(GmailService gmail, GmailSyncState state, CancellationToken cancellationToken)
    {
        if (state.WatchExpiresAt > DateTime.UtcNow.AddDays(1)) return;
        var watch = await gmail.Users.Watch(new WatchRequest { TopicName = _options.PubSubTopic, LabelIds = ["INBOX"], LabelFilterBehavior = "include" }, "me")
            .ExecuteAsync(cancellationToken);
        state.HistoryId = watch.HistoryId?.ToString() ?? state.HistoryId;
        state.WatchExpiresAt = watch.Expiration is null ? DateTime.UtcNow.AddDays(6) : DateTimeOffset.FromUnixTimeMilliseconds(watch.Expiration.Value).UtcDateTime;
    }

    private static async Task<HashSet<string>> GetChangedMessageIdsAsync(GmailService gmail, string historyId, CancellationToken cancellationToken)
    {
        var result = new HashSet<string>(StringComparer.Ordinal);
        try
        {
            var request = gmail.Users.History.List("me");
            if (!ulong.TryParse(historyId, out var checkpoint)) return result;
            request.StartHistoryId = checkpoint;
            request.HistoryTypes = UsersResource.HistoryResource.ListRequest.HistoryTypesEnum.MessageAdded;
            do
            {
                var page = await request.ExecuteAsync(cancellationToken);
                foreach (var history in page.History ?? [])
                    foreach (var added in history.MessagesAdded ?? [])
                        if (!string.IsNullOrWhiteSpace(added.Message.Id)) result.Add(added.Message.Id);
                request.PageToken = page.NextPageToken;
            } while (!string.IsNullOrWhiteSpace(request.PageToken));
        }
        catch (Google.GoogleApiException exception) when (exception.HttpStatusCode == System.Net.HttpStatusCode.NotFound)
        {
            // Gmail can expire old history IDs. Re-list INBOX before establishing the new baseline.
            var request = gmail.Users.Messages.List("me");
            do
            {
                var page = await request.ExecuteAsync(cancellationToken);
                foreach (var message in page.Messages ?? [])
                    if (!string.IsNullOrWhiteSpace(message.Id)) result.Add(message.Id);
                request.PageToken = page.NextPageToken;
            } while (!string.IsNullOrWhiteSpace(request.PageToken));
        }
        return result;
    }

    private async Task IngestAsync(Message message, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(message.Id)) return;
        // Transport headers such as Received legitimately occur more than once.
        var headers = message.Payload?.Headers?
            .Where(x => !string.IsNullOrWhiteSpace(x.Name))
            .GroupBy(x => x.Name!, StringComparer.OrdinalIgnoreCase)
            .ToDictionary(group => group.Key, group => group.Last().Value ?? string.Empty, StringComparer.OrdinalIgnoreCase)
            ?? [];
        headers.TryGetValue("From", out var sender); headers.TryGetValue("Subject", out var subject);
        if (string.IsNullOrWhiteSpace(sender)) return;
        var body = ExtractBody(message.Payload);
        var normalized = normalizer.Normalize(body);
        var receivedAt = message.InternalDate is long milliseconds ? DateTimeOffset.FromUnixTimeMilliseconds(milliseconds).UtcDateTime : DateTime.UtcNow;
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes($"{sender}|{subject}|{normalized.Text}|{receivedAt:O}")));
        if (await database.EmailSourceRecords.AnyAsync(x => (x.Mailbox == _options.ServiceMailbox && x.GmailMessageId == message.Id) || x.ContentHash == hash, cancellationToken)) return;

        headers.TryGetValue("Message-ID", out var internetMessageId);
        var record = new EmailSourceRecord { Mailbox = _options.ServiceMailbox, Folder = "INBOX", GmailMessageId = message.Id, GmailThreadId = message.ThreadId ?? string.Empty,
            SourceMessageId = message.Id, InternetMessageId = internetMessageId ?? string.Empty, ContentHash = hash, Sender = sender, Subject = subject ?? string.Empty, ReceivedAt = receivedAt };
        database.EmailSourceRecords.Add(record);
        await database.SaveChangesAsync(cancellationToken);
        await publisher.PublishAuditEventAsync(RabbitMqTopology.ReceivedRoutingKey, record.Id, new { record.Id, record.Sender, record.Subject, record.ReceivedAt }, cancellationToken);

        var decision = filter.Evaluate(sender, record.Subject, normalized.Text);
        if (!decision.Accepted)
        {
            record.Status = "Ignored"; record.IgnoreReason = decision.Reason;
            await database.SaveChangesAsync(cancellationToken);
            return;
        }
        record.Status = "Queued"; record.EmailAnalysisId = record.Id;
        await database.SaveChangesAsync(cancellationToken);
        await publisher.PublishAuditEventAsync(RabbitMqTopology.FilteredRoutingKey, record.Id, new { record.Id, record.Sender, record.Subject, normalized.Urls }, cancellationToken);
        await analyses.QueueAsync(new AnalyzeEmailRequest { EmailId = record.Id, Sender = sender, Subject = record.Subject, Body = normalized.Text, ReceivedAt = receivedAt }, cancellationToken);
        logger.LogInformation("Queued Gmail message {MessageId} for AI analysis", message.Id);
    }

    private static string ExtractBody(MessagePart? part)
    {
        if (part is null) return string.Empty;
        if (!string.IsNullOrWhiteSpace(part.Body?.Data)) return Encoding.UTF8.GetString(DecodeBase64Url(part.Body.Data));
        return string.Join("\n", part.Parts?.Select(ExtractBody) ?? []);
    }

    private static byte[] DecodeBase64Url(string value)
    {
        value = value.Replace('-', '+').Replace('_', '/');
        value = value.PadRight(value.Length + (4 - value.Length % 4) % 4, '=');
        return Convert.FromBase64String(value);
    }
}
