using IntegrationTracking.Api.Gmail;
using Microsoft.AspNetCore.Mvc;

namespace IntegrationTracking.Api.Controllers;

[ApiController]
[Route("api/gmail/oauth")]
public sealed class GmailOAuthController(GmailOAuthService oauth) : ControllerBase
{
    [HttpPost("bootstrap")]
    public async Task<IActionResult> Bootstrap(CancellationToken cancellationToken)
    {
        await oauth.BootstrapAsync(cancellationToken);
        return Ok(new { status = "authenticated", message = "Encrypted Gmail OAuth token cache is ready." });
    }
}
