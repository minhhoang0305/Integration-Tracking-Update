namespace IntegrationTracking.Api.Gmail;

public sealed record NormalizedEmail(string Text, List<string> Urls);
public sealed record FilterDecision(bool Accepted, string? Reason = null);
