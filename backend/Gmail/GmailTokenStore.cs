using System.Security.Cryptography;
using System.Text.Json;
using Google.Apis.Util.Store;

namespace IntegrationTracking.Api.Gmail;

// Google libraries only require IDataStore. Encrypting the serialized token keeps refresh tokens out of plaintext files.
public sealed class GmailTokenStore(string directory) : IDataStore
{
    private readonly string _directory = directory;

    public async Task StoreAsync<T>(string key, T value)
    {
        if (!OperatingSystem.IsWindows()) throw new PlatformNotSupportedException("Configure a production secret store outside Windows.");
        Directory.CreateDirectory(_directory);
        var protectedBytes = ProtectedData.Protect(JsonSerializer.SerializeToUtf8Bytes(value), null, DataProtectionScope.CurrentUser);
        await File.WriteAllBytesAsync(PathFor(key), protectedBytes);
    }

    public async Task<T> GetAsync<T>(string key)
    {
        if (!OperatingSystem.IsWindows()) throw new PlatformNotSupportedException("Configure a production secret store outside Windows.");
        var path = PathFor(key);
        if (!File.Exists(path)) return default!;
        var clearBytes = ProtectedData.Unprotect(await File.ReadAllBytesAsync(path), null, DataProtectionScope.CurrentUser);
        return JsonSerializer.Deserialize<T>(clearBytes)!;
    }

    public Task DeleteAsync<T>(string key)
    {
        var path = PathFor(key);
        if (File.Exists(path)) File.Delete(path);
        return Task.CompletedTask;
    }

    public Task ClearAsync()
    {
        if (Directory.Exists(_directory))
            foreach (var path in Directory.EnumerateFiles(_directory, "*.token")) File.Delete(path);
        return Task.CompletedTask;
    }

    private string PathFor(string key) => Path.Combine(_directory,
        Convert.ToHexString(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(key))) + ".token");
}
