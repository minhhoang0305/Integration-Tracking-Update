using Microsoft.Identity.Client;
using Microsoft.Identity.Client.Extensions.Msal;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Imap;

public sealed class ImapOAuthTokenService(IOptions<ImapOptions> options, ILogger<ImapOAuthTokenService> logger)
{
    private static readonly string[] Scopes = ["https://outlook.office.com/IMAP.AccessAsUser.All", "offline_access"];
    private readonly ImapOptions _options = options.Value;
    private Task<IPublicClientApplication>? _applicationTask;

    public async Task<string> AcquireAccessTokenAsync(CancellationToken cancellationToken)
    {
        if (!_options.IsConfigured)
            throw new InvalidOperationException("IMAP OAuth has not been configured.");

        var application = await GetApplicationAsync();
        var account = (await application.GetAccountsAsync()).FirstOrDefault();
        try
        {
            if (account is not null)
                return (await application.AcquireTokenSilent(Scopes, account).ExecuteAsync(cancellationToken)).AccessToken;
        }
        catch (MsalUiRequiredException)
        {
            // A device-code login below refreshes the local encrypted cache.
        }

        var result = await application.AcquireTokenWithDeviceCode(Scopes, code =>
        {
            logger.LogWarning("IMAP OAuth sign-in required: {Message}", code.Message);
            return Task.CompletedTask;
        }).ExecuteAsync(cancellationToken);
        return result.AccessToken;
    }

    private Task<IPublicClientApplication> GetApplicationAsync() =>
        _applicationTask ??= CreateApplicationAsync();

    private async Task<IPublicClientApplication> CreateApplicationAsync()
    {
        var application = PublicClientApplicationBuilder.Create(_options.ClientId)
            .WithTenantId(_options.TenantId)
            .Build();
        var cacheDirectory = string.IsNullOrWhiteSpace(_options.TokenCacheDirectory)
            ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "IntegrationTracking")
            : _options.TokenCacheDirectory;
        Directory.CreateDirectory(cacheDirectory);
        var storage = new StorageCreationPropertiesBuilder("imap-msal.cache", cacheDirectory).Build();
        var helper = await MsalCacheHelper.CreateAsync(storage);
        helper.RegisterCache(application.UserTokenCache);
        return application;
    }
}
