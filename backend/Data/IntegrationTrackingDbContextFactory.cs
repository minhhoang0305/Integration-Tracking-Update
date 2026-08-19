using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;
using Microsoft.Extensions.Configuration;

namespace IntegrationTracking.Api.Data;

public sealed class IntegrationTrackingDbContextFactory : IDesignTimeDbContextFactory<IntegrationTrackingDbContext>
{
    public IntegrationTrackingDbContext CreateDbContext(string[] args)
    {
        var configuration = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: false)
            .AddEnvironmentVariables()
            .Build();
        var connectionString = configuration.GetConnectionString("Postgres")
            ?? throw new InvalidOperationException("ConnectionStrings:Postgres is required.");
        return new IntegrationTrackingDbContext(
            new DbContextOptionsBuilder<IntegrationTrackingDbContext>().UseNpgsql(connectionString).Options);
    }
}
