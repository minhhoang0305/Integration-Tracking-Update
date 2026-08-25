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

    public static LineDiffDocument CreateLineDiff(string current, string proposed, int contextLines = 3)
    {
        var oldLines = Lines(current);
        var newLines = Lines(proposed);
        var lcs = new int[oldLines.Count + 1, newLines.Count + 1];
        for (var oldIndex = oldLines.Count - 1; oldIndex >= 0; oldIndex--)
            for (var newIndex = newLines.Count - 1; newIndex >= 0; newIndex--)
                lcs[oldIndex, newIndex] = oldLines[oldIndex] == newLines[newIndex]
                    ? lcs[oldIndex + 1, newIndex + 1] + 1
                    : Math.Max(lcs[oldIndex + 1, newIndex], lcs[oldIndex, newIndex + 1]);

        var lines = new List<LineDiffLine>();
        var oldPosition = 1; var newPosition = 1;
        for (int oldIndex = 0, newIndex = 0; oldIndex < oldLines.Count || newIndex < newLines.Count;)
        {
            if (oldIndex < oldLines.Count && newIndex < newLines.Count && oldLines[oldIndex] == newLines[newIndex])
                lines.Add(new("unchanged", oldPosition++, newPosition++, oldLines[oldIndex++]));
            else if (newIndex < newLines.Count && (oldIndex == oldLines.Count || lcs[oldIndex, newIndex + 1] >= lcs[oldIndex + 1, newIndex]))
                lines.Add(new("inserted", null, newPosition++, newLines[newIndex++]));
            else
                lines.Add(new("deleted", oldPosition++, null, oldLines[oldIndex++]));
        }

        var ranges = new List<(int Start, int End)>();
        foreach (var index in lines.Select((line, index) => (line, index)).Where(x => x.line.Kind != "unchanged").Select(x => x.index))
        {
            var start = Math.Max(0, index - contextLines); var end = Math.Min(lines.Count - 1, index + contextLines);
            if (ranges.Count > 0 && start <= ranges[^1].End + 1) ranges[^1] = (ranges[^1].Start, Math.Max(ranges[^1].End, end));
            else ranges.Add((start, end));
        }
        return new LineDiffDocument("actions_manifest.json", ranges.Select(range => ToHunk(lines, range.Start, range.End)).ToList());
    }

    public static string BuildUnifiedDiff(LineDiffDocument document)
    {
        var builder = new StringBuilder($"--- a/{document.FileName}\n+++ b/{document.FileName}\n");
        foreach (var hunk in document.Hunks)
        {
            builder.AppendLine($"@@ -{Range(hunk.OldStart, hunk.OldCount)} +{Range(hunk.NewStart, hunk.NewCount)} @@");
            foreach (var line in hunk.Lines) builder.Append(line.Kind == "deleted" ? '-' : line.Kind == "inserted" ? '+' : ' ').AppendLine(line.Text);
        }
        return builder.ToString();
    }

    private static LineDiffHunk ToHunk(IReadOnlyList<LineDiffLine> lines, int start, int end)
    {
        var selected = lines.Skip(start).Take(end - start + 1).ToList();
        var oldNumbers = selected.Where(x => x.Kind != "inserted" && x.OldLine.HasValue).Select(x => x.OldLine!.Value).ToList();
        var newNumbers = selected.Where(x => x.Kind != "deleted" && x.NewLine.HasValue).Select(x => x.NewLine!.Value).ToList();
        return new LineDiffHunk(oldNumbers.FirstOrDefault(), oldNumbers.Count, newNumbers.FirstOrDefault(), newNumbers.Count, selected);
    }

    private static string Range(int start, int count) => count == 1 ? start.ToString() : $"{start},{count}";
    private static List<string> Lines(string value) => value.Replace("\r\n", "\n").TrimEnd('\n').Split('\n').ToList();

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
public sealed record LineDiffDocument(string FileName, List<LineDiffHunk> Hunks);
public sealed record LineDiffHunk(int OldStart, int OldCount, int NewStart, int NewCount, List<LineDiffLine> Lines);
public sealed record LineDiffLine(string Kind, int? OldLine, int? NewLine, string Text);
