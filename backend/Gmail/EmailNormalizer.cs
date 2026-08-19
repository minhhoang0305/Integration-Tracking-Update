using System.Text.RegularExpressions;
using HtmlAgilityPack;

namespace IntegrationTracking.Api.Gmail;

public sealed class EmailNormalizer
{
    public NormalizedEmail Normalize(string body)
    {
        var html = new HtmlDocument();
        html.LoadHtml(body);
        var text = HtmlEntity.DeEntitize(html.DocumentNode.InnerText);
        text = Regex.Replace(text, @"(?im)^\s*(unsubscribe|manage preferences|privacy policy).*$", "");
        text = Regex.Split(text, @"(?im)^\s*(from:|on .* wrote:|-----original message-----)")[0];
        text = Regex.Replace(text, @"\s+", " ").Trim();
        var urls = Regex.Matches(body, @"https?://[^\s\""'<>]+", RegexOptions.IgnoreCase)
            .Select(x => x.Value.TrimEnd('.', ',', ')', ']')).Distinct(StringComparer.OrdinalIgnoreCase).ToList();
        return new NormalizedEmail(text, urls);
    }
}
