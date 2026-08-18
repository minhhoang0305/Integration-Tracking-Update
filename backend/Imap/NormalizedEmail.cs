namespace IntegrationTracking.Api.Imap;

public sealed record NormalizedEmail(string Text, IReadOnlyList<string> Urls);
public sealed record FilterDecision(bool Accepted, string? Reason)
{
    public static FilterDecision Accept() => new(true, null);
    public static FilterDecision Ignore(string reason) => new(false, reason);
}
