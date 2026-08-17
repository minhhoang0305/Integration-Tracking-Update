using IntegrationTracking.Api.Models;

namespace IntegrationTracking.Api.Services;

public sealed class EmailAnalysisService
{
    private readonly IEmailAnalyzer _emailAnalyzer;
    private readonly ILogger<EmailAnalysisService> _logger;

    public EmailAnalysisService(
        IEmailAnalyzer emailAnalyzer,
        ILogger<EmailAnalysisService> logger)
    {
        _emailAnalyzer = emailAnalyzer;
        _logger = logger;
    }

    public async Task<ChangeSignal> AnalyzeAsync(
        AnalyzeEmailRequest request,
        CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(request.Sender))
        {
            throw new ArgumentException(
                "Sender is required.",
                nameof(request.Sender));
        }

        if (string.IsNullOrWhiteSpace(request.Subject) &&
            string.IsNullOrWhiteSpace(request.Body))
        {
            throw new ArgumentException(
                "Email subject or body is required.");
        }

        _logger.LogInformation(
            "Starting analysis for email {EmailId}",
            request.EmailId);

        var result = await _emailAnalyzer.AnalyzeAsync(
            request,
            cancellationToken);

        _logger.LogInformation(
            "Finished analysis for email {EmailId}",
            request.EmailId);

        return result;
    }
}