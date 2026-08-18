namespace IntegrationTracking.Api.Imap;

public sealed class ImapIngestionWorker(IServiceScopeFactory scopeFactory, ILogger<ImapIngestionWorker> logger)
    : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                using var scope = scopeFactory.CreateScope();
                var service = scope.ServiceProvider.GetRequiredService<ImapMailService>();
                if (service.IsConfigured)
                    await service.SyncAndIdleAsync(stoppingToken);
                else
                    await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
            }
            catch (Exception exception)
            {
                logger.LogError(exception, "IMAP ingestion failed; retrying after the fallback interval.");
                await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
            }
        }
    }
}
