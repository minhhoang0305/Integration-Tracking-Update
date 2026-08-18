using IntegrationTracking.Api.Services;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Imap;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Logging.ClearProviders();
builder.Logging.AddConsole();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddDbContext<IntegrationTrackingDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Postgres")));
builder.Services.AddSingleton<RabbitMqConnection>();
builder.Services.AddSingleton<RabbitMqTopology>();
builder.Services.AddScoped<RabbitMqPublisher>();
builder.Services.AddScoped<EmailAnalysisService>();
builder.Services.AddHostedService<AnalysisResultConsumer>();
builder.Services.Configure<ImapOptions>(builder.Configuration.GetSection("Imap"));
builder.Services.AddScoped<ProviderEmailFilter>();
builder.Services.AddScoped<EmailNormalizer>();
builder.Services.AddSingleton<ImapOAuthTokenService>();
builder.Services.AddScoped<ImapMailService>();
builder.Services.AddHostedService<ImapIngestionWorker>();

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    scope.ServiceProvider.GetRequiredService<IntegrationTrackingDbContext>()
        .Database.Migrate();
}

app.UseSwagger();
app.UseSwaggerUI();

app.UseHttpsRedirection();

app.MapControllers();

app.MapGet("/health", () => Results.Ok(new
{
    status = "ok",
    service = "integration-tracking-api"
}));

app.Run();
