namespace IntegrationTracking.Api.Templates;

public sealed class TemplateOptions
{
    // Retained only to read historical proposals/configuration during migration to installed packages.
    public string RegistryPath { get; set; } = "Configuration/provider-integrations.json";
    public string IntegrationsRoot { get; set; } = "integrations/installed";
    public string ArtifactRoot { get; set; } = "proposals";
}

public sealed class ObjectStorageOptions
{
    public string ServiceUrl { get; set; } = string.Empty;
    public string AccessKey { get; set; } = string.Empty;
    public string SecretKey { get; set; } = string.Empty;
    public string CatalogBucket { get; set; } = "integration-catalog";
    public string ArtifactBucket { get; set; } = "proposal-artifacts";
}

public sealed class ProposalLlmOptions
{
    public string Endpoint { get; set; } = "https://api.openai.com/v1/chat/completions";
    public string ApiKey { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public bool IsConfigured => !string.IsNullOrWhiteSpace(ApiKey) && !string.IsNullOrWhiteSpace(Model);
}

public sealed class ProviderIntegrationRegistry { public List<ProviderRegistration> Providers { get; set; } = []; }
public sealed class ProviderRegistration
{
    public string Provider { get; set; } = string.Empty;
    public List<string> SenderDomains { get; set; } = [];
    public List<string> DocumentationDomains { get; set; } = [];
    public List<IntegrationRegistration> Integrations { get; set; } = [];
}
public sealed class IntegrationRegistration
{
    public string Id { get; set; } = string.Empty;
    public string ManifestPath { get; set; } = string.Empty;
    public string? VerifiedManifestPath { get; set; }
    public string ProposalMode { get; set; } = "llm";
}
