using IntegrationTracking.Api.Models;

namespace IntegrationTracking.Api.Templates;

public sealed class ImpactAnalysisService
{
    public IntegrationImpactAnalysis Analyze(string provider, string integrationId, ManifestDiff diff, ChangeSignal signal)
    {
        var deprecated = Endpoints(signal.DeprecatedEndpoints);
        var announced = Endpoints(signal.AnnouncedEndpoints);
        var affected = diff.RemovedActions.Select(action => new ImpactedAction(action.Name, action.HttpMethod, action.Endpoint,
            "RemovedAction", "High", "The current action is absent from the verified provider snapshot.", EvidenceStatus(action, deprecated))).ToList();
        affected.AddRange(diff.ChangedActions.Select(change => new ImpactedAction(change.Current.Name, change.Current.HttpMethod, change.Current.Endpoint,
            "ChangedAction", "Medium", "The verified provider snapshot changed this existing action.", EvidenceStatus(change.Current, deprecated, announced))));

        var newActions = diff.AddedActions.Select(action => new ImpactedAction(action.Name, action.HttpMethod, action.Endpoint,
            "AddedAction", "Low", "A new provider capability is available; no existing action is broken.", EvidenceStatus(action, announced))).ToList();
        var configChanges = diff.TopLevelChanges.Select(ConfigImpact).ToList();
        var allSeverities = affected.Concat(newActions).Select(x => x.Severity).Concat(configChanges.Select(x => x.Severity));
        return new IntegrationImpactAnalysis(provider, integrationId, diff.CurrentHash, diff.ProposedHash, HighestSeverity(allSeverities), affected, newActions, configChanges);
    }

    private static IntegrationConfigChange ConfigImpact(string property)
    {
        var severity = property is "base_url" or "auth_type" ? "Critical" : property is "executor" or "provider_config" ? "High" : "Medium";
        var reason = severity == "Critical" ? "Connection host or authentication behavior changed." : "Integration-level runtime configuration changed.";
        return new IntegrationConfigChange(property, severity, reason);
    }

    private static string EvidenceStatus(ManifestAction action, params HashSet<string>[] evidenceSets) =>
        evidenceSets.Any(set => set.Contains(Key(action.HttpMethod, action.Endpoint))) ? "MentionedInEmail" : "VerifiedSnapshotOnly";

    private static HashSet<string> Endpoints(IEnumerable<ApiEndpoint> endpoints) => endpoints.Select(x => Key(x.Method, x.Path)).ToHashSet(StringComparer.OrdinalIgnoreCase);
    private static string Key(string method, string path) => $"{method.ToUpperInvariant()} {path}";

    private static string HighestSeverity(IEnumerable<string> severities) => severities.OrderByDescending(SeverityRank).FirstOrDefault() ?? "Low";
    private static int SeverityRank(string severity) => severity switch { "Critical" => 4, "High" => 3, "Medium" => 2, "Low" => 1, _ => 0 };
}

public sealed record IntegrationImpactAnalysis(string Provider, string IntegrationId, string CurrentManifestHash, string ProposedManifestHash,
    string OverallSeverity, List<ImpactedAction> AffectedActions, List<ImpactedAction> NewActions, List<IntegrationConfigChange> IntegrationConfigChanges);
public sealed record ImpactedAction(string Name, string Method, string Endpoint, string ImpactType, string Severity, string Reason, string EvidenceStatus);
public sealed record IntegrationConfigChange(string Property, string Severity, string Reason);
