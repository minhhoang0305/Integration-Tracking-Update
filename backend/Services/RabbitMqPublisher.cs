using System.Text;
using System.Text.Json;
using IntegrationTracking.Api.Models;
using RabbitMQ.Client;

namespace IntegrationTracking.Api.Services;

public sealed class RabbitMqPublisher(RabbitMqConnection connection, RabbitMqTopology topology)
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    public Task PublishRequestedAsync(AnalyzeEmailRequest request, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        using var channel = connection.CreateChannel();
        topology.Declare(channel);
        Publish(channel, RabbitMqTopology.EventsExchange, RabbitMqTopology.RequestRoutingKey,
            new MessageEnvelope<AnalyzeEmailRequest> { CorrelationId = request.EmailId, Payload = request });
        return Task.CompletedTask;
    }

    public Task PublishAuditEventAsync<T>(string routingKey, string correlationId, T payload, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        using var channel = connection.CreateChannel();
        topology.Declare(channel);
        Publish(channel, RabbitMqTopology.EventsExchange, routingKey,
            new MessageEnvelope<T> { CorrelationId = correlationId, Payload = payload });
        return Task.CompletedTask;
    }

    private static void Publish<T>(IModel channel, string exchange, string routingKey, MessageEnvelope<T> envelope)
    {
        var properties = channel.CreateBasicProperties();
        properties.Persistent = true;
        properties.ContentType = "application/json";
        properties.CorrelationId = envelope.CorrelationId;
        channel.BasicPublish(exchange, routingKey, properties,
            Encoding.UTF8.GetBytes(JsonSerializer.Serialize(envelope, JsonOptions)));
    }
}
