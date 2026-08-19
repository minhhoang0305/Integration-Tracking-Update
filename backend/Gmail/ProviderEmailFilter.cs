using System.Text.RegularExpressions;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Gmail;

public sealed partial class ProviderEmailFilter(IOptions<GmailOptions> options)
{
    private readonly GmailOptions _options = options.Value;

    public FilterDecision Evaluate(string sender, string subject, string text)
    {
        var address = ExtractAddress(sender);
        var domain = address.Split('@').LastOrDefault()?.Trim().ToLowerInvariant();
        if (string.IsNullOrWhiteSpace(domain) || !_options.AllowedSenderDomains.Any(x =>
                domain.Equals(x, StringComparison.OrdinalIgnoreCase) || domain.EndsWith('.' + x, StringComparison.OrdinalIgnoreCase)))
            return new(false, "Sender domain is not allow-listed.");
        var content = $"{subject} {text}";
        if (AutoReplyRegex().IsMatch(content)) return new(false, "Auto-reply detected.");
        if (BounceRegex().IsMatch(content)) return new(false, "Delivery failure detected.");
        if (!ApiChangeRegex().IsMatch(content)) return new(false, "No provider API-change signal detected.");
        return new(true);
    }

    private static string ExtractAddress(string sender)
    {
        try { return new System.Net.Mail.MailAddress(sender).Address; }
        catch (FormatException)
        {
            var match = EmailAddressRegex().Match(sender);
            return match.Success ? match.Value : sender;
        }
    }

    [GeneratedRegex(@"\b(out of office|automatic reply|auto.?reply)\b", RegexOptions.IgnoreCase)]
    private static partial Regex AutoReplyRegex();
    [GeneratedRegex(@"\b(undeliverable|delivery status notification|mail delivery failed)\b", RegexOptions.IgnoreCase)]
    private static partial Regex BounceRegex();
    [GeneratedRegex(@"\b(deprecat|migration|api\s*v?\d|breaking change|endpoint|schema|oauth|authentication|rate limit|webhook|security update|sunset)\b", RegexOptions.IgnoreCase)]
    private static partial Regex ApiChangeRegex();
    [GeneratedRegex(@"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", RegexOptions.IgnoreCase)]
    private static partial Regex EmailAddressRegex();
}
