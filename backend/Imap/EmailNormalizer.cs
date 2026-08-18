using System.Net;
using System.Text.RegularExpressions;
using HtmlAgilityPack;

namespace IntegrationTracking.Api.Imap;

public sealed partial class EmailNormalizer
{
    public NormalizedEmail Normalize(string htmlOrText)
    {
        var document = new HtmlDocument();
        document.LoadHtml(htmlOrText);
        var text = WebUtility.HtmlDecode(document.DocumentNode.InnerText);
        text = QuotedReplyRegex().Replace(text, string.Empty);
        text = SignatureRegex().Replace(text, string.Empty);
        text = WhitespaceRegex().Replace(text, " ").Trim();
        var urls = UrlRegex().Matches(text).Select(x => x.Value).Distinct().ToList();
        return new NormalizedEmail(text, urls);
    }

    [GeneratedRegex(@"(?ms)^On .+?wrote:.*$")] private static partial Regex QuotedReplyRegex();
    [GeneratedRegex(@"(?ms)\n--\s*\n.*$")] private static partial Regex SignatureRegex();
    [GeneratedRegex(@"\s+")] private static partial Regex WhitespaceRegex();
    [GeneratedRegex(@"https?://[^\s)]+", RegexOptions.IgnoreCase)] private static partial Regex UrlRegex();
}
