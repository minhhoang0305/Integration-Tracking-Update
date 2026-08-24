using System.Text;
using System.Text.Json;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Models;
using IntegrationTracking.Api.Templates;
using Microsoft.EntityFrameworkCore;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;

namespace IntegrationTracking.Api.Services;

public sealed class AnalysisResultConsumer(
    RabbitMqConnection connection,
    RabbitMqTopology topology,
    IServiceScopeFactory scopeFactory,
    RabbitMqPublisher publisher,
    InstalledIntegrationCatalog catalog,
    ILogger<AnalysisResultConsumer> logger) : BackgroundService
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var channel = connection.CreateChannel();
        topology.Declare(channel);
        channel.BasicQos(0, 1, false);
        var consumer = new EventingBasicConsumer(channel);
        consumer.Received += (_, args) => Handle(channel, args);
        channel.BasicConsume(RabbitMqTopology.BackendQueue, autoAck: false, consumer);
        await Task.Delay(Timeout.Infinite, stoppingToken);
    }

    private void Handle(IModel channel, BasicDeliverEventArgs args)
    {
        try
        {
            var body = Encoding.UTF8.GetString(args.Body.ToArray());
            using var scope = scopeFactory.CreateScope();
                var database = scope.ServiceProvider.GetRequiredService<IntegrationTrackingDbContext>();
            var proposals = scope.ServiceProvider.GetRequiredService<IntegrationTracking.Api.Templates.TemplateProposalService>();

            if (args.RoutingKey == RabbitMqTopology.CompletedRoutingKey)
            {
                var message = JsonSerializer.Deserialize<MessageEnvelope<ChangeSignal>>(body, JsonOptions)
                    ?? throw new JsonException("Completed event is empty.");
                var analysis = database.EmailAnalyses.Find(message.CorrelationId);
                if (analysis is not null && analysis.Status != AnalysisStatuses.Completed)
                {
                    var resolution = catalog.Resolve(analysis, message.Payload);
                    var provider = resolution.Integration?.Provider ?? (resolution.Status == "Ambiguous" ? "ambiguous" : "unknown");
                    var integrationId = resolution.Integration?.IntegrationId;
                    var providerUpdate = new ProviderUpdateEvent
                    {
                        EventId = analysis.EmailId,
                        EmailId = analysis.EmailId,
                        Provider = provider,
                        IntegrationId = integrationId,
                        Source = new ProviderEmailSource
                        {
                            Sender = analysis.Sender,
                            Subject = analysis.Subject,
                            ReceivedAt = analysis.ReceivedAt
                        },
                        ChangeTypes = message.Payload.ChangeTypes,
                        Summary = message.Payload.Summary,
                        Confidence = message.Payload.Confidence,
                        Evidence = message.Payload.Evidence
                    };
                    if (message.Payload.ChangeDetected)
                    {
                        publisher.PublishAuditEventAsync(RabbitMqTopology.ProviderUpdateRoutingKey,
                            analysis.EmailId, providerUpdate, CancellationToken.None).GetAwaiter().GetResult();
                    }
                    analysis.Status = AnalysisStatuses.Completed;
                    analysis.ResultJson = JsonSerializer.Serialize(message.Payload, JsonOptions);
                    analysis.ErrorMessage = null;
                    analysis.UpdatedAt = DateTime.UtcNow;
                    var source = database.EmailSourceRecords.Find(analysis.EmailId);
                    if (source is not null) source.Status = "Completed";
                    database.SaveChanges();
                    proposals.GenerateAsync(analysis, message.Payload, CancellationToken.None).GetAwaiter().GetResult();
                }
                logger.LogInformation("Analysis {EmailId} completed.", message.CorrelationId);
            }
            else if (args.RoutingKey == RabbitMqTopology.FailedRoutingKey)
            {
                var message = JsonSerializer.Deserialize<MessageEnvelope<AnalysisFailedPayload>>(body, JsonOptions)
                    ?? throw new JsonException("Failed event is empty.");
                var analysis = database.EmailAnalyses.Find(message.CorrelationId);
                if (analysis is not null && analysis.Status != AnalysisStatuses.Completed)
                {
                    analysis.Status = AnalysisStatuses.Failed;
                    analysis.ErrorMessage = message.Payload.Error;
                    analysis.UpdatedAt = DateTime.UtcNow;
                    var source = database.EmailSourceRecords.Find(analysis.EmailId);
                    if (source is not null) source.Status = "Failed";
                    database.SaveChanges();
                }
                logger.LogWarning("Analysis {EmailId} failed after {Attempts} attempts.",
                    message.CorrelationId, message.Payload.Attempts);
            }

            channel.BasicAck(args.DeliveryTag, false);
        }
        catch (Exception exception)
        {
            logger.LogError(exception, "Unable to process RabbitMQ result event.");
            channel.BasicNack(args.DeliveryTag, false, requeue: true);
        }
    }
}
