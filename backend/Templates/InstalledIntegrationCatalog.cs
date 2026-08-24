using System.Text.Json;
using System.Text.RegularExpressions;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Models;

namespace IntegrationTracking.Api.Templates;

/// <summary>Reads active integration packages exclusively from the S3 catalog.</summary>
public sealed class InstalledIntegrationCatalog(IIntegrationStorage storage)
{
    public IReadOnlyList<InstalledIntegration> Load()
    {
        var integrations = storage.ListIntegrationIds().Select(folder =>
        {
            using var manifest = JsonDocument.Parse(storage.ReadIntegrationText(folder, "actions_manifest.json"));
            ManifestDiffService.ValidateManifest(manifest.RootElement);
            var provider = Text(manifest.RootElement, "provider");
            if (string.IsNullOrWhiteSpace(provider)) throw new InvalidOperationException($"S3 integration package '{folder}' has no provider field.");
            var urls = UrlHosts(manifest.RootElement).Concat(GuideHosts(folder)).Distinct(StringComparer.OrdinalIgnoreCase).ToList();
            return new InstalledIntegration(provider, folder, folder, urls);
        }).ToList();
        var duplicates = integrations.GroupBy(x => x.Provider, StringComparer.OrdinalIgnoreCase).Where(x => x.Count() > 1).ToList();
        if (duplicates.Count > 0) throw new InvalidOperationException("Installed integration providers must be unique: " + string.Join(", ", duplicates.Select(x => x.Key)));
        return integrations;
    }

    public InstalledIntegration? Find(string provider, string integrationId) => Load().FirstOrDefault(x => x.Provider.Equals(provider, StringComparison.OrdinalIgnoreCase) && x.IntegrationId.Equals(integrationId, StringComparison.OrdinalIgnoreCase));
    public string ReadManifest(string integrationId) => storage.ReadIntegrationText(integrationId, "actions_manifest.json");

    public IntegrationResolution Resolve(EmailAnalysis analysis, ChangeSignal signal)
    {
        var urls = Hosts(signal.DocumentationUrls.Concat(signal.Evidence.Urls).Concat(UrlsIn(analysis.Subject + "\n" + analysis.Body)));
        var candidates = Load().Select(x => Score(x, urls, analysis.Subject, analysis.Body)).Where(x => x.Score > 0).OrderByDescending(x => x.Score).ThenBy(x => x.Integration.Provider).ToList();
        var top = candidates.FirstOrDefault();
        if (top is null || top.Score < 60) return new("Unknown", null, candidates, urls, "No integration has enough URL or provider-name evidence.");
        if (candidates.Count > 1 && candidates[1].Score == top.Score) return new("Ambiguous", null, candidates, urls, "More than one integration has the highest evidence score.");
        return new("Resolved", top.Integration, candidates, urls, "A single integration has the highest evidence score.");
    }

    private IEnumerable<string> GuideHosts(string id)
    {
        try { using var guide = JsonDocument.Parse(storage.ReadIntegrationText(id, "connect_guide.json")); return UrlHosts(guide.RootElement).ToList(); }
        catch (FileNotFoundException) { return []; }
    }
    private static ResolutionCandidate Score(InstalledIntegration i, IReadOnlyList<string> hosts, string subject, string body)
    {
        var evidence = new List<string>(); var score = 0;
        foreach (var host in hosts.Where(host => i.UrlHosts.Any(domain => host.Equals(domain, StringComparison.OrdinalIgnoreCase) || host.EndsWith('.' + domain, StringComparison.OrdinalIgnoreCase)))) { score += 100; evidence.Add("url:" + host); }
        if (Phrase(subject, i.Provider) || Phrase(subject, i.IntegrationId)) { score += 70; evidence.Add("subject:provider-name"); }
        if (Phrase(body, i.Provider) || Phrase(body, i.IntegrationId)) { score += 50; evidence.Add("body:provider-name"); }
        return new(i, score, evidence);
    }
    private static bool Phrase(string text, string phrase) => phrase.Length >= 3 && Regex.IsMatch(text, $@"(?<![A-Za-z0-9]){Regex.Escape(phrase).Replace("\\-", "[-_ ]").Replace("\\_", "[-_ ]")}(?![A-Za-z0-9])", RegexOptions.IgnoreCase);
    private static IEnumerable<string> UrlsIn(string text) => Regex.Matches(text, @"https?://[^\s)\]}>]+", RegexOptions.IgnoreCase).Select(x => x.Value);
    private static IReadOnlyList<string> Hosts(IEnumerable<string> values) => values.Select(value => Uri.TryCreate(value, UriKind.Absolute, out var uri) ? uri.Host.ToLowerInvariant() : null).Where(x => x is not null).Cast<string>().Distinct(StringComparer.OrdinalIgnoreCase).ToList();
    private static IEnumerable<string> UrlHosts(JsonElement element) { foreach (var value in Strings(element)) if (Uri.TryCreate(value, UriKind.Absolute, out var uri)) yield return uri.Host.ToLowerInvariant(); }
    private static IEnumerable<string> Strings(JsonElement element) { if (element.ValueKind == JsonValueKind.String) { yield return element.GetString() ?? ""; yield break; } if (element.ValueKind == JsonValueKind.Object) foreach (var p in element.EnumerateObject()) foreach (var v in Strings(p.Value)) yield return v; if (element.ValueKind == JsonValueKind.Array) foreach (var x in element.EnumerateArray()) foreach (var v in Strings(x)) yield return v; }
    private static string Text(JsonElement element, string name) => element.TryGetProperty(name, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() ?? "" : "";
}

public sealed record InstalledIntegration(string Provider, string IntegrationId, string Folder, IReadOnlyList<string> UrlHosts);
public sealed record ResolutionCandidate(InstalledIntegration Integration, int Score, IReadOnlyList<string> Evidence);
public sealed record IntegrationResolution(string Status, InstalledIntegration? Integration, IReadOnlyList<ResolutionCandidate> Candidates, IReadOnlyList<string> UrlHosts, string Reason);
