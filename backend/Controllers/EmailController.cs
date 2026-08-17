using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace IntegrationTracking.Api.Controllers;

[ApiController]
[Route("api/emails")]
public sealed class EmailController : ControllerBase
{
    private readonly EmailAnalysisService _emailAnalysisService;
    private readonly ILogger<EmailController> _logger;

    public EmailController(
        EmailAnalysisService emailAnalysisService,
        ILogger<EmailController> logger)
    {
        _emailAnalysisService = emailAnalysisService;
        _logger = logger;
    }

    [HttpPost("analyze")]
    [ProducesResponseType(typeof(ChangeSignal), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status502BadGateway)]
    [ProducesResponseType(StatusCodes.Status504GatewayTimeout)]
    [ProducesResponseType(StatusCodes.Status500InternalServerError)]
    public async Task<ActionResult<ChangeSignal>> Analyze(
        [FromBody] AnalyzeEmailRequest request,
        CancellationToken cancellationToken)
    {
        try
        {
            var result = await _emailAnalysisService.AnalyzeAsync(
                request,
                cancellationToken);

            return Ok(result);
        }
        catch (ArgumentException exception)
        {
            return BadRequest(new
            {
                error = exception.Message
            });
        }
        catch (TimeoutException exception)
        {
            return StatusCode(
                StatusCodes.Status504GatewayTimeout,
                new
                {
                    error = exception.Message
                });
        }
        catch (HttpRequestException exception)
        {
            return StatusCode(
                StatusCodes.Status502BadGateway,
                new
                {
                    error = "Python analyzer is unavailable.",
                    detail = exception.Message
                });
        }
        catch (Exception exception)
        {
            _logger.LogError(
                exception,
                "Unexpected error while analyzing email {EmailId}",
                request.EmailId);

            return StatusCode(
                StatusCodes.Status500InternalServerError,
                new
                {
                    error = "Unexpected internal server error."
                });
        }
    }
}