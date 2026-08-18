using RabbitMQ.Client;

namespace IntegrationTracking.Api.Services;

public sealed class RabbitMqTopology
{
    public const string EventsExchange = "integration-tracking.events";
    public const string RetryExchange = "integration-tracking.retry";
    public const string RequestRoutingKey = "email.analysis.requested";
    public const string ReceivedRoutingKey = "email.received";
    public const string FilteredRoutingKey = "email.filtered";
    public const string ProviderUpdateRoutingKey = "provider.update.detected";
    public const string CompletedRoutingKey = "email.analysis.completed";
    public const string FailedRoutingKey = "email.analysis.failed";
    public const string DeadLetterRoutingKey = "email.analysis.dlq";
    public const string WorkerQueue = "email.analysis.worker";
    public const string BackendQueue = "email.analysis.backend";
    public const string DeadLetterQueue = "email.analysis.dlq";
    public const string ProviderUpdateQueue = "provider.update.handoff";

    public void Declare(IModel channel)
    {
        channel.ExchangeDeclare(EventsExchange, ExchangeType.Topic, durable: true);
        channel.ExchangeDeclare(RetryExchange, ExchangeType.Direct, durable: true);
        channel.QueueDeclare(WorkerQueue, durable: true, exclusive: false, autoDelete: false);
        channel.QueueBind(WorkerQueue, EventsExchange, RequestRoutingKey);
        channel.QueueDeclare(BackendQueue, durable: true, exclusive: false, autoDelete: false);
        channel.QueueBind(BackendQueue, EventsExchange, CompletedRoutingKey);
        channel.QueueBind(BackendQueue, EventsExchange, FailedRoutingKey);
        channel.QueueDeclare(DeadLetterQueue, durable: true, exclusive: false, autoDelete: false);
        channel.QueueBind(DeadLetterQueue, EventsExchange, DeadLetterRoutingKey);
        channel.QueueDeclare(ProviderUpdateQueue, durable: true, exclusive: false, autoDelete: false);
        channel.QueueBind(ProviderUpdateQueue, EventsExchange, ProviderUpdateRoutingKey);

        DeclareRetryQueue(channel, 10);
        DeclareRetryQueue(channel, 30);
        DeclareRetryQueue(channel, 60);
    }

    private static void DeclareRetryQueue(IModel channel, int seconds)
    {
        var queueName = $"email.analysis.retry.{seconds}s";
        var arguments = new Dictionary<string, object>
        {
            ["x-message-ttl"] = seconds * 1000,
            ["x-dead-letter-exchange"] = EventsExchange,
            ["x-dead-letter-routing-key"] = RequestRoutingKey
        };
        channel.QueueDeclare(queueName, durable: true, exclusive: false, autoDelete: false, arguments);
        channel.QueueBind(queueName, RetryExchange, $"retry.{seconds}");
    }
}
