using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Templates;
using Xunit;

namespace IntegrationTracking.Api.Tests;

public sealed class InstalledIntegrationCatalogTests
{
    [Fact]
    public void Load_ReadsAllInstalledManifestsWithUniqueProviders()
    {
        var catalog = Catalog();
        var integrations = catalog.Load();

        Assert.True(integrations.Count >= 84);
        Assert.Equal(integrations.Count, integrations.Select(x => x.Provider).Distinct(StringComparer.OrdinalIgnoreCase).Count());
        Assert.Contains(integrations, x => x.Provider == "u301" && x.IntegrationId == "u301");
    }

    [Fact]
    public void Resolve_UsesOfficialDocumentationUrlInsteadOfGmailSender()
    {
        var resolution = Catalog().Resolve(new EmailAnalysis
        {
            Sender = "Personal Gmail <hoang7620345@gmail.com>",
            Subject = "U301 API endpoint update",
            Body = "See https://docs.u301.com/ for migration details."
        }, new ChangeSignal { ChangeDetected = true, DocumentationUrls = ["https://docs.u301.com/"] });

        Assert.Equal("Resolved", resolution.Status);
        Assert.Equal("u301", resolution.Integration?.Provider);
        Assert.Equal("u301", resolution.Integration?.IntegrationId);
    }

    [Fact]
    public void Resolve_WithoutProviderEvidence_ReturnsUnknownInsteadOfGuessingFromGmail()
    {
        var resolution = Catalog().Resolve(new EmailAnalysis
        {
            Sender = "Personal Gmail <hoang7620345@gmail.com>",
            Subject = "Important platform update",
            Body = "Please review the following API changes."
        }, new ChangeSignal { ChangeDetected = true });

        Assert.Equal("Unknown", resolution.Status);
        Assert.Null(resolution.Integration);
    }

    private static InstalledIntegrationCatalog Catalog()
    {
        var root = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../integrations/installed"));
        return new InstalledIntegrationCatalog(new TestStorage(root));
    }

    private sealed class TestStorage(string root) : IIntegrationStorage
    {
        public Task ValidateCatalogAsync(CancellationToken ct = default) => Task.CompletedTask;
        public IReadOnlyList<string> ListIntegrationIds() => Directory.EnumerateDirectories(root).Select(Path.GetFileName).Where(x => x is not null).Cast<string>().ToList();
        public string ReadIntegrationText(string integrationId, string name) => File.ReadAllText(Path.Combine(root, integrationId, name));
        public Task WriteProposalTextAsync(string proposalId, string name, string content, CancellationToken ct) => Task.CompletedTask;
        public string? ReadProposalText(string proposalId, string name) => null;
    }
}
