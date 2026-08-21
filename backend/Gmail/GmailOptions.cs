namespace IntegrationTracking.Api.Gmail;

public sealed class GmailOptions
{
    public bool Enabled { get; set; } = true;
    public string ClientId { get; set; } = string.Empty;
    public string ClientSecret { get; set; } = string.Empty;
    public string ServiceMailbox { get; set; } = string.Empty;
    public string PubSubTopic { get; set; } = string.Empty;
    public string TokenCacheDirectory { get; set; } = string.Empty;
    // Base64-encoded 32-byte key. Set through User Secrets or an environment variable, never appsettings.json.
    public string TokenEncryptionKey { get; set; } = string.Empty;
    public int PollingIntervalMinutes { get; set; } = 5;
    public List<string> AllowedSenderDomains { get; set; } = [];

    public bool IsConfigured => !string.IsNullOrWhiteSpace(ClientId)
        && !string.IsNullOrWhiteSpace(ClientSecret)
        && !string.IsNullOrWhiteSpace(ServiceMailbox)
        && !string.IsNullOrWhiteSpace(PubSubTopic)
        && !string.IsNullOrWhiteSpace(TokenEncryptionKey);
}
