using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Templates;

public sealed record LlmProposal(JsonElement Manifest, string Changelog, string Risk);

public sealed class ProposalLlmClient(HttpClient http, IOptions<ProposalLlmOptions> options)
{
    private readonly ProposalLlmOptions _options = options.Value;
    public async Task<LlmProposal> GenerateAsync(string provider, string integrationId, string currentManifest, IReadOnlyList<string> evidence, CancellationToken cancellationToken)
    {
        if (!_options.IsConfigured) throw new InvalidOperationException("Proposal LLM is not configured.");
        var prompt = $$"""
            You update an integration action manifest. Return ONLY JSON: {"manifest": object, "changelog": string, "risk": string}.
            Preserve unknown fields and only propose changes supported by the evidence. Never invent endpoints, authentication settings, or fields.
            Provider: {{provider}}
            Integration: {{integrationId}}
            Current manifest: {{currentManifest}}
            Documentation evidence: {{string.Join("\n---\n", evidence)}}
            """;
        using var request = new HttpRequestMessage(HttpMethod.Post, _options.Endpoint);
        request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", _options.ApiKey);
        request.Content = JsonContent.Create(new { model = _options.Model, response_format = new { type = "json_object" }, messages = new[] { new { role = "user", content = prompt } } });
        using var response = await http.SendAsync(request, cancellationToken);
        response.EnsureSuccessStatusCode();
        using var envelope = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancellationToken));
        var content = envelope.RootElement.GetProperty("choices")[0].GetProperty("message").GetProperty("content").GetString() ?? throw new JsonException("LLM returned no content.");
        using var result = JsonDocument.Parse(content);
        var root = result.RootElement;
        return new LlmProposal(root.GetProperty("manifest").Clone(), root.GetProperty("changelog").GetString() ?? string.Empty, root.GetProperty("risk").GetString() ?? "Unknown");
    }
}
