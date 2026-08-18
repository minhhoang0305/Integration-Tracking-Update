using System.Security.Cryptography;
using System.Text;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Services;
using MailKit;
using MailKit.Net.Imap;
using MailKit.Search;
using MailKit.Security;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using MimeKit;

namespace IntegrationTracking.Api.Imap;

public sealed class ImapMailService(
    ImapOAuthTokenService tokenService,
    IntegrationTrackingDbContext database,
    ProviderEmailFilter filter,
    EmailNormalizer normalizer,
    EmailAnalysisService emailAnalysisService,
    RabbitMqPublisher publisher,
    IOptions<ImapOptions> options,
    ILogger<ImapMailService> logger)
{
    private readonly ImapOptions _options = options.Value;
    public bool IsConfigured => _options.IsConfigured;

    public async Task SyncAndIdleAsync(CancellationToken cancellationToken)
    {
        if (!IsConfigured)
            return;

        var token = await tokenService.AcquireAccessTokenAsync(cancellationToken);
        using var client = new ImapClient();
        await client.ConnectAsync(_options.Host, _options.Port, SecureSocketOptions.SslOnConnect, cancellationToken);
        await client.AuthenticateAsync(new SaslMechanismOAuth2(_options.ServiceMailbox, token), cancellationToken);
        var folder = await client.GetFolderAsync(_options.Folder, cancellationToken);
        await folder.OpenAsync(FolderAccess.ReadOnly, cancellationToken);
        await SynchronizeFolderAsync(folder, cancellationToken);

        using var idleCancellation = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        idleCancellation.CancelAfter(TimeSpan.FromMinutes(Math.Max(1, _options.PollingIntervalMinutes)));
        try
        {
            await client.IdleAsync(idleCancellation.Token);
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            // Timed IDLE reconnect provides a polling fallback without modifying the mailbox.
        }
        finally
        {
            await client.DisconnectAsync(true, CancellationToken.None);
        }
    }

    private async Task SynchronizeFolderAsync(IMailFolder folder, CancellationToken cancellationToken)
    {
        var uidValidity = (long)folder.UidValidity;
        var state = await database.ImapSyncStates.FindAsync([_options.ServiceMailbox, _options.Folder], cancellationToken);
        if (state is null)
        {
            state = new ImapSyncState { Mailbox = _options.ServiceMailbox, Folder = _options.Folder, UidValidity = uidValidity };
            database.ImapSyncStates.Add(state);
            await database.SaveChangesAsync(cancellationToken);
        }
        else if (state.UidValidity != uidValidity)
        {
            // IMAP UIDs are only meaningful inside one UIDVALIDITY epoch.
            state.UidValidity = uidValidity;
            state.LastUid = 0;
            state.UpdatedAt = DateTime.UtcNow;
            await database.SaveChangesAsync(cancellationToken);
        }

        var uids = await folder.SearchAsync(SearchQuery.All, cancellationToken);
        foreach (var uid in uids.Where(x => (long)x.Id > state.LastUid).OrderBy(x => x.Id))
        {
            var message = await folder.GetMessageAsync(uid, cancellationToken);
            await IngestAsync(message, uidValidity, (long)uid.Id, cancellationToken);
            state.LastUid = (long)uid.Id;
            state.UpdatedAt = DateTime.UtcNow;
            await database.SaveChangesAsync(cancellationToken);
        }
    }

    private async Task IngestAsync(MimeMessage message, long uidValidity, long imapUid, CancellationToken cancellationToken)
    {
        var sender = message.From.Mailboxes.FirstOrDefault()?.Address;
        if (string.IsNullOrWhiteSpace(sender))
            return;

        var body = message.HtmlBody ?? message.TextBody ?? string.Empty;
        var normalized = normalizer.Normalize(body);
        var receivedAt = message.Date == DateTimeOffset.MinValue ? DateTime.UtcNow : message.Date.UtcDateTime;
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(
            $"{sender}|{message.Subject}|{normalized.Text}|{receivedAt:O}")));
        if (await database.EmailSourceRecords.AnyAsync(x =>
            (x.Mailbox == _options.ServiceMailbox && x.Folder == _options.Folder &&
             x.UidValidity == uidValidity && x.ImapUid == imapUid) || x.ContentHash == hash, cancellationToken))
            return;

        var record = new EmailSourceRecord
        {
            Mailbox = _options.ServiceMailbox,
            Folder = _options.Folder,
            UidValidity = uidValidity,
            ImapUid = imapUid,
            SourceMessageId = $"{uidValidity}:{imapUid}",
            InternetMessageId = message.MessageId ?? string.Empty,
            ContentHash = hash,
            Sender = sender,
            Subject = message.Subject ?? string.Empty,
            ReceivedAt = receivedAt
        };
        database.EmailSourceRecords.Add(record);
        await database.SaveChangesAsync(cancellationToken);
        await publisher.PublishAuditEventAsync(RabbitMqTopology.ReceivedRoutingKey, record.Id,
            new { record.Id, record.Sender, record.Subject, record.ReceivedAt }, cancellationToken);

        var decision = filter.Evaluate(sender, record.Subject, normalized.Text);
        if (!decision.Accepted)
        {
            record.Status = "Ignored";
            record.IgnoreReason = decision.Reason;
            await database.SaveChangesAsync(cancellationToken);
            logger.LogInformation("Ignored IMAP message {MessageId}: {Reason}", record.Id, decision.Reason);
            return;
        }

        record.Status = "Queued";
        record.EmailAnalysisId = record.Id;
        await database.SaveChangesAsync(cancellationToken);
        await publisher.PublishAuditEventAsync(RabbitMqTopology.FilteredRoutingKey, record.Id,
            new { record.Id, record.Sender, record.Subject, Urls = normalized.Urls }, cancellationToken);
        await emailAnalysisService.QueueAsync(new AnalyzeEmailRequest
        {
            EmailId = record.Id,
            Sender = sender,
            Subject = record.Subject,
            Body = normalized.Text,
            ReceivedAt = record.ReceivedAt
        }, cancellationToken);
        logger.LogInformation("Queued IMAP message {MessageId} for AI analysis", record.Id);
    }
}
