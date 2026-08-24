using Amazon.Runtime;
using Amazon.S3;
using Amazon.S3.Model;
using Microsoft.Extensions.Options;
using System.Text.Json;

namespace IntegrationTracking.Api.Templates;

public interface IIntegrationStorage
{
    Task ValidateCatalogAsync(CancellationToken ct = default);
    IReadOnlyList<string> ListIntegrationIds();
    string ReadIntegrationText(string integrationId, string name);
    Task WriteProposalTextAsync(string proposalId, string name, string content, CancellationToken ct);
    string? ReadProposalText(string proposalId, string name);
}

public sealed class S3IntegrationStorage : IIntegrationStorage, IDisposable
{
    private readonly ObjectStorageOptions _options;
    private readonly IAmazonS3 _s3;

    public S3IntegrationStorage(IOptions<ObjectStorageOptions> options)
    {
        _options = options.Value;
        if (string.IsNullOrWhiteSpace(_options.ServiceUrl) || string.IsNullOrWhiteSpace(_options.AccessKey) || string.IsNullOrWhiteSpace(_options.SecretKey))
            throw new InvalidOperationException("ObjectStorage ServiceUrl, AccessKey, and SecretKey are required for S3-only runtime.");
        _s3 = new AmazonS3Client(new BasicAWSCredentials(_options.AccessKey, _options.SecretKey), new AmazonS3Config
        {
            ServiceURL = _options.ServiceUrl,
            ForcePathStyle = true,
            UseHttp = _options.ServiceUrl.StartsWith("http://", StringComparison.OrdinalIgnoreCase)
        });
    }

    public async Task ValidateCatalogAsync(CancellationToken ct = default)
    {
        if (!await BucketExistsAsync(_options.CatalogBucket, ct)) throw new InvalidOperationException($"S3 catalog bucket '{_options.CatalogBucket}' does not exist.");
        if (!await BucketExistsAsync(_options.ArtifactBucket, ct)) throw new InvalidOperationException($"S3 artifact bucket '{_options.ArtifactBucket}' does not exist.");
        var integrations = ListIntegrationIds();
        if (integrations.Count == 0) throw new InvalidOperationException("S3 catalog is empty. Run the MinIO seed service before starting the backend.");
        foreach (var integration in integrations)
        {
            using var manifest = JsonDocument.Parse(ReadIntegrationText(integration, "actions_manifest.json"));
            ManifestDiffService.ValidateManifest(manifest.RootElement);
        }
    }

    public IReadOnlyList<string> ListIntegrationIds()
    {
        var response = _s3.ListObjectsV2Async(new ListObjectsV2Request { BucketName = _options.CatalogBucket, Prefix = "integrations/", Delimiter = "/" }).GetAwaiter().GetResult();
        return response.CommonPrefixes.Select(prefix => prefix.TrimEnd('/').Split('/').Last()).OrderBy(x => x, StringComparer.OrdinalIgnoreCase).ToList();
    }

    public string ReadIntegrationText(string integrationId, string name) => Read(_options.CatalogBucket, $"integrations/{SafeSegment(integrationId)}/{SafeName(name)}")
        ?? throw new FileNotFoundException($"S3 integration object was not found: {integrationId}/{name}");

    public async Task WriteProposalTextAsync(string proposalId, string name, string content, CancellationToken ct)
    {
        await _s3.PutObjectAsync(new PutObjectRequest { BucketName = _options.ArtifactBucket, Key = $"proposals/{SafeSegment(proposalId)}/{SafeName(name)}", ContentBody = content, ContentType = "application/json" }, ct);
    }

    public string? ReadProposalText(string proposalId, string name) => Read(_options.ArtifactBucket, $"proposals/{SafeSegment(proposalId)}/{SafeName(name)}");

    private string? Read(string bucket, string key)
    {
        try
        {
            using var response = _s3.GetObjectAsync(bucket, key).GetAwaiter().GetResult();
            using var reader = new StreamReader(response.ResponseStream);
            return reader.ReadToEnd();
        }
        catch (AmazonS3Exception exception) when (exception.StatusCode == System.Net.HttpStatusCode.NotFound) { return null; }
    }

    private async Task<bool> BucketExistsAsync(string bucket, CancellationToken ct)
    {
        try { await _s3.GetBucketLocationAsync(new GetBucketLocationRequest { BucketName = bucket }, ct); return true; }
        catch (AmazonS3Exception exception) when (exception.StatusCode == System.Net.HttpStatusCode.NotFound) { return false; }
    }

    private static string SafeSegment(string value) => !string.IsNullOrWhiteSpace(value) && value.All(c => char.IsLetterOrDigit(c) || c is '-' or '_') ? value : throw new InvalidOperationException("Storage key segment is invalid.");
    private static string SafeName(string value) => !value.Contains("..", StringComparison.Ordinal) && !value.Contains('/') && !value.Contains('\\') ? value : throw new InvalidOperationException("Storage object name is invalid.");
    public void Dispose() => _s3.Dispose();
}
