using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace IntegrationTracking.Api.Controllers;

[ApiController]
[Route("api/emails")]
public sealed class EmailController(EmailAnalysisService emailAnalysisService) : ControllerBase
{
    [HttpPost("analyze")]
    [ProducesResponseType(typeof(AnalysisStatusResponse), StatusCodes.Status202Accepted)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status502BadGateway)]
    public async Task<ActionResult<AnalysisStatusResponse>> Analyze(
        [FromBody] AnalyzeEmailRequest request,
        CancellationToken cancellationToken)
    {
        try
        {
            var result = await emailAnalysisService.QueueAsync(request, cancellationToken);
            return AcceptedAtAction(nameof(GetStatus), new { emailId = result.EmailId }, result);
        }
        catch (ArgumentException exception)
        {
            return BadRequest(new { error = exception.Message });
        }
        catch (Exception exception)
        {
            return StatusCode(StatusCodes.Status502BadGateway, new
            {
                error = "Message broker is unavailable.", detail = exception.Message
            });
        }
    }

    [HttpGet("/api/email-analyses/{emailId}")]
    [ProducesResponseType(typeof(AnalysisStatusResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<AnalysisStatusResponse>> GetStatus(
        string emailId,
        CancellationToken cancellationToken)
    {
        var result = await emailAnalysisService.GetStatusAsync(emailId, cancellationToken);
        return result is null ? NotFound() : Ok(result);
    }
}
