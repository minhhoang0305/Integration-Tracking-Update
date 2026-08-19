using HtmlAgilityPack;

namespace IntegrationTracking.Api.Templates;

public sealed class DocumentationEvidenceService(HttpClient http)
{
    public async Task<List<string>> ReadAsync(IEnumerable<string> urls, IEnumerable<string> allowedDomains, CancellationToken cancellationToken)
    {
        var domains = allowedDomains.ToList();
        var evidence = new List<string>();
        foreach (var raw in urls.Distinct(StringComparer.OrdinalIgnoreCase).Take(5))
        {
            if (!Uri.TryCreate(raw, UriKind.Absolute, out var uri) || uri.Scheme != Uri.UriSchemeHttps || !domains.Any(x => uri.Host.Equals(x, StringComparison.OrdinalIgnoreCase) || uri.Host.EndsWith('.' + x, StringComparison.OrdinalIgnoreCase))) continue;
            using var response = await http.GetAsync(uri, cancellationToken);
            if (!response.IsSuccessStatusCode) continue;
            var document = new HtmlDocument(); document.LoadHtml(await response.Content.ReadAsStringAsync(cancellationToken));
            var text = HtmlEntity.DeEntitize(document.DocumentNode.InnerText).Trim();
            if (!string.IsNullOrWhiteSpace(text)) evidence.Add($"Source: {uri}\n{text[..Math.Min(text.Length, 12000)]}");
        }
        return evidence;
    }
}
