using System;
using System.IO;
using IntegrationTracking.Api.Templates;
using Xunit;

namespace IntegrationTracking.Api.Tests;

public sealed class ManifestDiffServiceTests
{
    [Fact]
    public void Compare_U301Snapshots_ReportsExpectedChanges()
    {
        var fixtureRoot = Path.Combine(AppContext.BaseDirectory, "fixtures");
        var current = File.ReadAllText(Path.Combine(fixtureRoot, "actions_manifest.old.json"));
        var proposed = File.ReadAllText(Path.Combine(fixtureRoot, "actions_manifest.new.json"));

        var diff = new ManifestDiffService().Compare(current, proposed);

        Assert.Equal(8, diff.RemovedActions.Count);
        Assert.Equal(10, diff.AddedActions.Count);
        Assert.Empty(diff.ChangedActions);
        Assert.Contains("executor", diff.TopLevelChanges);
        Assert.Contains("provider_config", diff.TopLevelChanges);
        Assert.DoesNotContain("base_url", diff.TopLevelChanges);
        Assert.Contains(diff.AddedActions, action => action.HttpMethod == "POST" && action.Endpoint == "/v3/shorten/bulk");
    }
}
