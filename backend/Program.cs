using IntegrationTracking.Api.Services;
using IntegrationTracking.Api.Data;
using IntegrationTracking.Api.Gmail;
using IntegrationTracking.Api.Templates;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);
// Local secrets are outside the repository. Production must provide the same values through its secret store/environment.
builder.Configuration.AddUserSecrets<Program>(optional: true);
// Environment variables must override local User Secrets so Docker/local profiles can disable Gmail safely.
builder.Configuration.AddEnvironmentVariables();

builder.Logging.ClearProviders();
builder.Logging.AddConsole();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddDbContext<IntegrationTrackingDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Postgres")));
builder.Services.AddSingleton<RabbitMqConnection>();
builder.Services.AddSingleton<RabbitMqTopology>();
builder.Services.AddSingleton<RabbitMqPublisher>();
builder.Services.AddScoped<EmailAnalysisService>();
builder.Services.AddHostedService<AnalysisResultConsumer>();
builder.Services.Configure<GmailOptions>(builder.Configuration.GetSection("Gmail"));
builder.Services.Configure<TemplateOptions>(builder.Configuration.GetSection("Templates"));
builder.Services.Configure<ProposalLlmOptions>(builder.Configuration.GetSection("ProposalLlm"));
builder.Services.AddScoped<ProviderEmailFilter>();
builder.Services.AddScoped<EmailNormalizer>();
builder.Services.AddSingleton<GmailOAuthService>();
builder.Services.AddSingleton<GmailSyncTrigger>();
builder.Services.AddScoped<GmailIngestionService>();
if (builder.Configuration.GetValue<bool?>("Gmail:Enabled") ?? true)
    builder.Services.AddHostedService<GmailIngestionWorker>();
builder.Services.AddSingleton<TemplateRegistryService>();
builder.Services.AddSingleton<ManifestDiffService>();
builder.Services.AddSingleton<ImpactAnalysisService>();
builder.Services.AddHttpClient<DocumentationEvidenceService>();
builder.Services.AddHttpClient<ProposalLlmClient>();
builder.Services.AddScoped<TemplateProposalService>();

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
