using IntegrationTracking.Api.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddScoped<EmailAnalysisService>();

builder.Services.AddHttpClient<IEmailAnalyzer, PythonAnalyzerClient>(
    client =>
    {
        var baseUrl =
            builder.Configuration["PythonService:BaseUrl"]
            ?? "http://localhost:8000";

        client.BaseAddress = new Uri(baseUrl);

        client.Timeout = TimeSpan.FromSeconds(30);
    });

var app = builder.Build();

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