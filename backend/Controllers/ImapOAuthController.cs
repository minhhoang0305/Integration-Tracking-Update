using IntegrationTracking.Api.Imap;
using Microsoft.AspNetCore.Mvc;

namespace IntegrationTracking.Api.Controllers;

[ApiController]
[Route("api/imap/oauth")]
public sealed class ImapOAuthController(ImapOAuthTokenService tokenService) : ControllerBase
{
    [HttpPost("bootstrap")]
    public async Task<IActionResult> Bootstrap(CancellationToken cancellationToken)
    {
        await tokenService.AcquireAccessTokenAsync(cancellationToken);
        return Ok(new { status = "authenticated", message = "Encrypted local token cache is ready." });
    }
}
