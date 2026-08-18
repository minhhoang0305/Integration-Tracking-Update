namespace IntegrationTracking.Api.Imap;

public sealed class ImapOptions
{
    public string TenantId { get; init; } = string.Empty;
    public string ClientId { get; init; } = string.Empty;
    public string ServiceMailbox { get; init; } = string.Empty;
    public string Host { get; init; } = "outlook.office365.com";
    public int Port { get; init; } = 993;
    public string Folder { get; init; } = "INBOX";
    public string TokenCacheDirectory { get; init; } = string.Empty;
    public int PollingIntervalMinutes { get; init; } = 5;
    public string[] AllowedSenderDomains { get; init; } = [];

    public bool IsConfigured => !string.IsNullOrWhiteSpace(TenantId) &&
        !string.IsNullOrWhiteSpace(ClientId) && !string.IsNullOrWhiteSpace(ServiceMailbox);
}
