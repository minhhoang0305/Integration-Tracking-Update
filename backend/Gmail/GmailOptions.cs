namespace IntegrationTracking.Api.Gmail;

public sealed class GmailOptions
{
    public string ClientId { get; set; } = string.Empty;
    public string ClientSecret { get; set; } = string.Empty;
    public string ServiceMailbox { get; set; } = string.Empty;
    public string PubSubTopic { get; set; } = string.Empty;
    public string TokenCacheDirectory { get; set; } = string.Empty;
    public int PollingIntervalMinutes { get; set; } = 5;
    public List<string> AllowedSenderDomains { get; set; } = [];

    public bool IsConfigured => !string.IsNullOrWhiteSpace(ClientId)
        && !string.IsNullOrWhiteSpace(ClientSecret)
        && !string.IsNullOrWhiteSpace(ServiceMailbox)
        && !string.IsNullOrWhiteSpace(PubSubTopic);
}
