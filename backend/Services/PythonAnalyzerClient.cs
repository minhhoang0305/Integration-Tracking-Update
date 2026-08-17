using System.Net.Http.Json;
using System.Text.Json;
using IntegrationTracking.Api.Models;

namespace IntegrationTracking.Api.Services;

public sealed class PythonAnalyzerClient : IEmailAnalyzer
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<PythonAnalyzerClient> _logger;

    public PythonAnalyzerClient(
        HttpClient httpClient,
        ILogger<PythonAnalyzerClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task<ChangeSignal> AnalyzeAsync(
        AnalyzeEmailRequest request,
        CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation(
                "Sending email {EmailId} to Python analyzer",
                request.EmailId);

            using var response = await _httpClient.PostAsJsonAsync(
                "/analyze",
                request,
                cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                var errorBody = await response.Content.ReadAsStringAsync(
                    cancellationToken);

                _logger.LogError(
                    "Python analyzer returned {StatusCode}. Response: {Response}",
                    response.StatusCode,
                    errorBody);

                throw new HttpRequestException(
                    $"Python analyzer returned HTTP {(int)response.StatusCode}.");
            }

            var result = await response.Content.ReadFromJsonAsync<ChangeSignal>(
                cancellationToken: cancellationToken);

            if (result is null)
            {
                throw new InvalidOperationException(
                    "Python analyzer returned an empty response.");
            }

            _logger.LogInformation(
                "Email {EmailId} analyzed successfully. ChangeDetected={ChangeDetected}",
                request.EmailId,
                result.ChangeDetected);

            return result;
        }
        catch (TaskCanceledException)
            when (!cancellationToken.IsCancellationRequested)
        {
            _logger.LogError(
                "Python analyzer timed out for email {EmailId}",
                request.EmailId);

            throw new TimeoutException(
                "Python analyzer request timed out.");
        }
        catch (HttpRequestException exception)
        {
            _logger.LogError(
                exception,
                "Cannot communicate with Python analyzer for email {EmailId}",
                request.EmailId);

            throw;
        }
        catch (JsonException exception)
        {
            _logger.LogError(
                exception,
                "Invalid JSON returned by Python analyzer.");

            throw new InvalidOperationException(
                "Python analyzer returned an invalid response.",
                exception);
        }
    }
}