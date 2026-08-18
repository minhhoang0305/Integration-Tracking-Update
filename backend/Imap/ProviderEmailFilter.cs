using System.Text.RegularExpressions;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Imap;

public sealed partial class ProviderEmailFilter(IOptions<ImapOptions> options)
{
    private readonly HashSet<string> _allowedDomains = options.Value.AllowedSenderDomains
        .Select(x => x.Trim().ToLowerInvariant()).Where(x => x.Length > 0).ToHashSet();

    public FilterDecision Evaluate(string sender, string subject, string text)
    {
        var domain = sender.Split('@').LastOrDefault()?.Trim().ToLowerInvariant();
        if (string.IsNullOrEmpty(domain) || !_allowedDomains.Contains(domain))
            return FilterDecision.Ignore("Sender domain is not an approved provider.");
        if (AutomatedMessageRegex().IsMatch(subject))
            return FilterDecision.Ignore("Automated mailbox message.");
        if (!ApiChangeRegex().IsMatch($"{subject} {text}"))
            return FilterDecision.Ignore("No API-change indicator.");
        return FilterDecision.Accept();
    }

    [GeneratedRegex(@"\b(out of office|automatic reply|delivery failed|undeliverable)\b", RegexOptions.IgnoreCase)]
    private static partial Regex AutomatedMessageRegex();
    [GeneratedRegex(@"\b(deprecat|migration|api\s*v?\d|endpoint|webhook|rate limit|schema|oauth|breaking change|sunset)\b", RegexOptions.IgnoreCase)]
    private static partial Regex ApiChangeRegex();
}
