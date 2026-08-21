using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace IntegrationTracking.Api.Templates;

public sealed class ManifestDiffService
{
    public ManifestDiff Compare(string currentJson, string proposedJson)
    {
        using var current = JsonDocument.Parse(currentJson);
        using var proposed = JsonDocument.Parse(proposedJson);
        ValidateManifest(current.RootElement);
        ValidateManifest(proposed.RootElement);

        var currentActions = ReadActions(current.RootElement);
        var proposedActions = ReadActions(proposed.RootElement);
        var removed = currentActions.Keys.Except(proposedActions.Keys).OrderBy(x => x).Select(x => currentActions[x]).ToList();
        var added = proposedActions.Keys.Except(currentActions.Keys).OrderBy(x => x).Select(x => proposedActions[x]).ToList();
        var changed = currentActions.Keys.Intersect(proposedActions.Keys).OrderBy(x => x)
            .Where(x => !JsonNode.DeepEquals(JsonNode.Parse(currentActions[x].RawJson), JsonNode.Parse(proposedActions[x].RawJson)))
            .Select(x => new ChangedManifestAction(currentActions[x], proposedActions[x])).ToList();

        var topLevelChanges = current.RootElement.EnumerateObject().Where(x => x.Name != "actions")
            .Select(x => x.Name).Union(proposed.RootElement.EnumerateObject().Where(x => x.Name != "actions").Select(x => x.Name))
            .Where(name => !ElementsEqual(current.RootElement, proposed.RootElement, name)).OrderBy(x => x).ToList();

        return new ManifestDiff(
            Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(currentJson))),
            Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(proposedJson))),
            removed, added, changed, topLevelChanges);
    }

    public static void ValidateManifest(JsonElement manifest)
    {
        if (manifest.ValueKind != JsonValueKind.Object || !manifest.TryGetProperty("actions", out var actions) || actions.ValueKind != JsonValueKind.Array)
            throw new InvalidOperationException("Manifest must be an object containing an actions array.");
        foreach (var action in actions.EnumerateArray())
        {
            if (action.ValueKind != JsonValueKind.Object || !StringProperty(action, "name") || !StringProperty(action, "http_method") ||
                !StringProperty(action, "endpoint") || !action.TryGetProperty("input_schema", out var schema) || schema.ValueKind != JsonValueKind.Object)
                throw new InvalidOperationException("Every action must contain name, http_method, endpoint, and object input_schema.");
        }
    }

    public static string BuildUnifiedDiff(string current, string proposed) =>
        $"--- a/actions_manifest.json\n+++ b/actions_manifest.json\n@@ -1,{current.Split('\n').Length} +1,{proposed.Split('\n').Length} @@\n" +
        string.Join('\n', current.Split('\n').Select(x => "-" + x)) + "\n" +
        string.Join('\n', proposed.Split('\n').Select(x => "+" + x)) + "\n";

    private static Dictionary<string, ManifestAction> ReadActions(JsonElement manifest) => manifest.GetProperty("actions").EnumerateArray()
        .Select(action => new ManifestAction(action.GetProperty("name").GetString()!, action.GetProperty("http_method").GetString()!, action.GetProperty("endpoint").GetString()!, action.GetRawText()))
        .ToDictionary(action => $"{action.HttpMethod} {action.Endpoint}", StringComparer.OrdinalIgnoreCase);

    private static bool ElementsEqual(JsonElement current, JsonElement proposed, string property)
    {
        var hasCurrent = current.TryGetProperty(property, out var currentValue);
        var hasProposed = proposed.TryGetProperty(property, out var proposedValue);
        return hasCurrent == hasProposed && (!hasCurrent || JsonNode.DeepEquals(JsonNode.Parse(currentValue.GetRawText()), JsonNode.Parse(proposedValue.GetRawText())));
    }

    private static bool StringProperty(JsonElement element, string property) =>
        element.TryGetProperty(property, out var value) && value.ValueKind == JsonValueKind.String && !string.IsNullOrWhiteSpace(value.GetString());
}

public sealed record ManifestAction(string Name, string HttpMethod, string Endpoint, string RawJson);
public sealed record ChangedManifestAction(ManifestAction Current, ManifestAction Proposed);
public sealed record ManifestDiff(string CurrentHash, string ProposedHash, List<ManifestAction> RemovedActions,
    List<ManifestAction> AddedActions, List<ChangedManifestAction> ChangedActions, List<string> TopLevelChanges);
