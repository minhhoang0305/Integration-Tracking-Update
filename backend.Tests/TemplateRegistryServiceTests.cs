using IntegrationTracking.Api.Templates;
using Xunit;

namespace IntegrationTracking.Api.Tests;

public sealed class TemplateRegistryServiceTests
{
    [Theory]
    [InlineData("u301-notify@gmail.com", "gmail.com")]
    [InlineData("U301 API Team <u301-notify@gmail.com>", "gmail.com")]
    [InlineData("malformed display <u301-notify@gmail.com", "gmail.com")]
    public void SenderDomain_NormalizesMailboxAndDisplayName(string sender, string expected)
    {
        Assert.Equal(expected, TemplateRegistryService.SenderDomain(sender));
    }
}
