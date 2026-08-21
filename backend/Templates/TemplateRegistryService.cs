using System.Text.Json;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Templates;

public sealed class TemplateRegistryService(IHostEnvironment environment, IOptions<TemplateOptions> options)
{
    private readonly TemplateOptions _options = options.Value;
    private readonly string _contentRoot = Path.GetFullPath(environment.ContentRootPath);
    private readonly string _workspaceRoot = FindWorkspaceRoot(environment.ContentRootPath);
    public ProviderIntegrationRegistry Load()
    {
        var path = ContentPath(_options.RegistryPath);
        if (!File.Exists(path)) return new ProviderIntegrationRegistry();
        return JsonSerializer.Deserialize<ProviderIntegrationRegistry>(File.ReadAllText(path), new JsonSerializerOptions(JsonSerializerDefaults.Web)) ?? new ProviderIntegrationRegistry();
    }
    public ProviderRegistration? FindProvider(string sender)
    {
        var domain = SenderDomain(sender);
        return Load().Providers.FirstOrDefault(x => x.SenderDomains.Any(allowed => domain.Equals(allowed, StringComparison.OrdinalIgnoreCase) || domain.EndsWith('.' + allowed, StringComparison.OrdinalIgnoreCase)));
    }

    public static string SenderDomain(string sender)
    {
        try { return new System.Net.Mail.MailAddress(sender).Host.ToLowerInvariant(); }
        catch (FormatException)
        {
            var match = System.Text.RegularExpressions.Regex.Match(sender, @"[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})", System.Text.RegularExpressions.RegexOptions.IgnoreCase);
            return match.Success ? match.Groups[1].Value.ToLowerInvariant() : string.Empty;
        }
    }
    public string ContentPath(string relativePath) => SafePath(_contentRoot, relativePath);

    public string WorkspacePath(string relativePath) => SafePath(_workspaceRoot, relativePath);

    private static string FindWorkspaceRoot(string contentRoot)
    {
        var root = Path.GetFullPath(contentRoot);
        var parent = Directory.GetParent(root)?.FullName;
        return parent is not null && Directory.Exists(Path.Combine(parent, "integrations")) ? parent : root;
    }

    private static string SafePath(string root, string relativePath)
    {
        var path = Path.GetFullPath(Path.Combine(root, relativePath));
        if (!path.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("Template path escapes content root.");
        return path;
    }
}
