using System;
using System.IO;
using System.Linq;
using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Templates;
using Xunit;

namespace IntegrationTracking.Api.Tests;

public sealed class ImpactAnalysisServiceTests
{
    [Fact]
    public void Analyze_U301FullEmail_ReportsImpactsAndEmailEvidence()
    {
        var diff = U301Diff();
        var signal = new ChangeSignal
        {
            DeprecatedEndpoints = diff.RemovedActions.Select(Endpoint).ToList(),
            AnnouncedEndpoints = diff.AddedActions.Select(Endpoint).ToList()
        };

        var impact = new ImpactAnalysisService().Analyze("u301", "u301-shortener", diff, signal);

        Assert.Equal("u301", impact.Provider);
        Assert.Equal("u301-shortener", impact.IntegrationId);
        Assert.Equal("High", impact.OverallSeverity);
        Assert.Equal(8, impact.AffectedActions.Count);
        Assert.All(impact.AffectedActions, action =>
        {
            Assert.Equal("RemovedAction", action.ImpactType);
            Assert.Equal("High", action.Severity);
            Assert.Equal("MentionedInEmail", action.EvidenceStatus);
        });
        Assert.Equal(10, impact.NewActions.Count);
        Assert.All(impact.NewActions, action =>
        {
            Assert.Equal("AddedAction", action.ImpactType);
            Assert.Equal("Low", action.Severity);
            Assert.Equal("MentionedInEmail", action.EvidenceStatus);
        });
        Assert.DoesNotContain(impact.IntegrationConfigChanges, change => change.Property is "base_url" or "auth_type");
        Assert.Contains(impact.IntegrationConfigChanges, change => change.Property == "executor" && change.Severity == "High");
        Assert.Contains(impact.IntegrationConfigChanges, change => change.Property == "provider_config" && change.Severity == "High");
    }

    [Fact]
    public void Analyze_U301PartialEmail_PreservesVerifiedSnapshotOnlyEvidence()
    {
        var diff = U301Diff();
        var signal = new ChangeSignal
        {
            DeprecatedEndpoints = [Endpoint(diff.RemovedActions[0])],
            AnnouncedEndpoints = [Endpoint(diff.AddedActions[0])]
        };

        var impact = new ImpactAnalysisService().Analyze("u301", "u301-shortener", diff, signal);

        Assert.Equal(1, impact.AffectedActions.Count(action => action.EvidenceStatus == "MentionedInEmail"));
        Assert.Equal(7, impact.AffectedActions.Count(action => action.EvidenceStatus == "VerifiedSnapshotOnly"));
        Assert.Equal(1, impact.NewActions.Count(action => action.EvidenceStatus == "MentionedInEmail"));
        Assert.Equal(9, impact.NewActions.Count(action => action.EvidenceStatus == "VerifiedSnapshotOnly"));
    }

    private static ManifestDiff U301Diff()
    {
        var root = Path.Combine(AppContext.BaseDirectory, "fixtures");
        return new ManifestDiffService().Compare(
            File.ReadAllText(Path.Combine(root, "actions_manifest.old.json")),
            File.ReadAllText(Path.Combine(root, "actions_manifest.new.json")));
    }

    private static ApiEndpoint Endpoint(ManifestAction action) => new() { Method = action.HttpMethod, Path = action.Endpoint };
}
