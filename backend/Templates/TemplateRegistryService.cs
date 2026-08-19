using System.Text.Json;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Templates;

public sealed class TemplateRegistryService(IHostEnvironment environment, IOptions<TemplateOptions> options)
{
    private readonly TemplateOptions _options = options.Value;
    public ProviderIntegrationRegistry Load()
    {
        var path = AbsolutePath(_options.RegistryPath);
        if (!File.Exists(path)) return new ProviderIntegrationRegistry();
        return JsonSerializer.Deserialize<ProviderIntegrationRegistry>(File.ReadAllText(path), new JsonSerializerOptions(JsonSerializerDefaults.Web)) ?? new ProviderIntegrationRegistry();
    }
    public ProviderRegistration? FindProvider(string sender)
    {
        var domain = sender.Split('@').LastOrDefault() ?? string.Empty;
        return Load().Providers.FirstOrDefault(x => x.SenderDomains.Any(allowed => domain.Equals(allowed, StringComparison.OrdinalIgnoreCase) || domain.EndsWith('.' + allowed, StringComparison.OrdinalIgnoreCase)));
    }
    public string AbsolutePath(string relativePath)
    {
        var root = Path.GetFullPath(environment.ContentRootPath);
        var path = Path.GetFullPath(Path.Combine(root, relativePath));
        if (!path.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("Template path escapes content root.");
        return path;
    }
}
