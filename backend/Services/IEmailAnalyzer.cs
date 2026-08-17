using IntegrationTracking.Api.Models;

namespace IntegrationTracking.Api.Services;

public interface IEmailAnalyzer
{
    Task<ChangeSignal> AnalyzeAsync(
        AnalyzeEmailRequest request,
        CancellationToken cancellationToken = default);
}