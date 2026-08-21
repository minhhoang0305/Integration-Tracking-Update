using Google.Apis.Auth.OAuth2;
using Google.Apis.Auth.OAuth2.Responses;
using Google.Apis.Auth.OAuth2.Flows;
using Google.Apis.Util.Store;
using Microsoft.Extensions.Options;

namespace IntegrationTracking.Api.Gmail;

public sealed class GmailOAuthService(IOptions<GmailOptions> options)
{
    public const string ReadonlyScope = "https://www.googleapis.com/auth/gmail.readonly";
    private readonly GmailOptions _options = options.Value;
    private UserCredential? _credential;

    public bool IsConfigured => _options.IsConfigured;

    public async Task<UserCredential> GetCredentialAsync(CancellationToken cancellationToken)
    {
        if (!IsConfigured) throw new InvalidOperationException("Gmail OAuth has not been configured.");
        if (_credential is not null) return _credential;

        var directory = string.IsNullOrWhiteSpace(_options.TokenCacheDirectory)
            ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "IntegrationTracking", "gmail")
            : _options.TokenCacheDirectory;
        var flow = new GoogleAuthorizationCodeFlow(new GoogleAuthorizationCodeFlow.Initializer
        {
            ClientSecrets = new ClientSecrets { ClientId = _options.ClientId, ClientSecret = _options.ClientSecret },
            Scopes = [ReadonlyScope],
            DataStore = new GmailTokenStore(directory, _options.TokenEncryptionKey)
        });
        var token = await flow.LoadTokenAsync(_options.ServiceMailbox, cancellationToken);
        if (token is null || string.IsNullOrWhiteSpace(token.RefreshToken))
            throw new InvalidOperationException("Gmail OAuth bootstrap is required. Run POST /api/gmail/oauth/bootstrap locally.");

        _credential = new UserCredential(flow, _options.ServiceMailbox, token);
        if (!await _credential.RefreshTokenAsync(cancellationToken))
            throw new InvalidOperationException("Gmail refresh token could not be refreshed. Run OAuth bootstrap again.");
        return _credential;
    }

    public async Task BootstrapAsync(CancellationToken cancellationToken)
    {
        if (!IsConfigured) throw new InvalidOperationException("Gmail OAuth has not been configured.");
        var directory = string.IsNullOrWhiteSpace(_options.TokenCacheDirectory)
            ? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "IntegrationTracking", "gmail")
            : _options.TokenCacheDirectory;
        var flow = new GoogleAuthorizationCodeFlow(new GoogleAuthorizationCodeFlow.Initializer
        {
            ClientSecrets = new ClientSecrets { ClientId = _options.ClientId, ClientSecret = _options.ClientSecret },
            Scopes = [ReadonlyScope], DataStore = new GmailTokenStore(directory, _options.TokenEncryptionKey)
        });
        var receiver = new LocalServerCodeReceiver();
        _credential = await new AuthorizationCodeInstalledApp(flow, receiver)
            .AuthorizeAsync(_options.ServiceMailbox, cancellationToken);
    }
}
