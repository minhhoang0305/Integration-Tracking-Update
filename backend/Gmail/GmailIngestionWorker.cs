namespace IntegrationTracking.Api.Gmail;

public sealed class GmailIngestionWorker(IServiceScopeFactory scopes, GmailSyncTrigger trigger, ILogger<GmailIngestionWorker> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                using var scope = scopes.CreateScope();
                var service = scope.ServiceProvider.GetRequiredService<GmailIngestionService>();
                if (service.IsConfigured) await service.SynchronizeAsync(stoppingToken);
                await trigger.WaitAsync(TimeSpan.FromMinutes(5), stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { }
            catch (Exception exception)
            {
                logger.LogError(exception, "Gmail synchronization failed.");
                await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
            }
        }
    }
}
