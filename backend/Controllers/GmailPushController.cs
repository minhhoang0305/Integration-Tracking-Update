using System.Text;
using System.Text.Json;
using IntegrationTracking.Api.Gmail;
using Microsoft.AspNetCore.Mvc;

namespace IntegrationTracking.Api.Controllers;

[ApiController]
[Route("api/gmail/push")]
public sealed class GmailPushController(GmailSyncTrigger trigger, ILogger<GmailPushController> logger) : ControllerBase
{
    [HttpPost]
    public IActionResult Receive([FromBody] JsonElement payload)
    {
        // Pub/Sub already authenticates the push subscription; payload is decoded only for traceability.
        if (payload.TryGetProperty("message", out var message) && message.TryGetProperty("data", out var data))
        {
            try
            {
                var encoded = data.GetString()!.Replace('-', '+').Replace('_', '/');
                encoded = encoded.PadRight(encoded.Length + (4 - encoded.Length % 4) % 4, '=');
                logger.LogInformation("Received Gmail Pub/Sub notification: {Notification}", Encoding.UTF8.GetString(Convert.FromBase64String(encoded)));
            }
            catch (FormatException) { logger.LogWarning("Received Gmail Pub/Sub notification with invalid data."); }
        }
        trigger.Trigger();
        return Ok();
    }
}
