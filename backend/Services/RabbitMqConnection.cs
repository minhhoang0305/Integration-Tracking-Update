using RabbitMQ.Client;

namespace IntegrationTracking.Api.Services;

public sealed class RabbitMqConnection : IDisposable
{
    private readonly IConnection _connection;

    public RabbitMqConnection(IConfiguration configuration)
    {
        var factory = new ConnectionFactory
        {
            HostName = configuration["RabbitMq:Host"] ?? "localhost",
            Port = configuration.GetValue<int?>("RabbitMq:Port") ?? 5672,
            UserName = configuration["RabbitMq:UserName"] ?? "guest",
            Password = configuration["RabbitMq:Password"] ?? "guest",
            DispatchConsumersAsync = false
        };
        _connection = factory.CreateConnection();
    }

    public IModel CreateChannel() => _connection.CreateModel();

    public void Dispose() => _connection.Dispose();
}
