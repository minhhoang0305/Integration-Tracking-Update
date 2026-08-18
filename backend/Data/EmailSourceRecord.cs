namespace IntegrationTracking.Api.Data;

public sealed class EmailSourceRecord
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Mailbox { get; set; } = string.Empty;
    public string Folder { get; set; } = "INBOX";
    public long UidValidity { get; set; }
    public long ImapUid { get; set; }
    public string SourceMessageId { get; set; } = string.Empty;
    public string InternetMessageId { get; set; } = string.Empty;
    public string ContentHash { get; set; } = string.Empty;
    public string Sender { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string Status { get; set; } = "Received";
    public string? IgnoreReason { get; set; }
    public string? EmailAnalysisId { get; set; }
    public DateTime ReceivedAt { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public sealed class ImapSyncState
{
    public string Mailbox { get; set; } = string.Empty;
    public string Folder { get; set; } = "INBOX";
    public long UidValidity { get; set; }
    public long LastUid { get; set; }
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
