using System.Security.Cryptography;
using System.Text.Json;
using Google.Apis.Util.Store;

namespace IntegrationTracking.Api.Gmail;

// Google libraries only require IDataStore. Encrypting the serialized token keeps refresh tokens out of plaintext files.
public sealed class GmailTokenStore(string directory, string base64EncryptionKey) : IDataStore
{
    private const byte FormatVersion = 1;
    private const int NonceSize = 12;
    private const int TagSize = 16;
    private readonly string _directory = directory;
    private readonly byte[] _encryptionKey = ParseEncryptionKey(base64EncryptionKey);

    public async Task StoreAsync<T>(string key, T value)
    {
        Directory.CreateDirectory(_directory);
        RestrictDirectoryPermissions(_directory);

        var plaintext = JsonSerializer.SerializeToUtf8Bytes(value);
        var nonce = RandomNumberGenerator.GetBytes(NonceSize);
        var ciphertext = new byte[plaintext.Length];
        var tag = new byte[TagSize];
        using (var aes = new AesGcm(_encryptionKey, TagSize))
            aes.Encrypt(nonce, plaintext, ciphertext, tag);

        var payload = new byte[1 + NonceSize + TagSize + ciphertext.Length];
        payload[0] = FormatVersion;
        Buffer.BlockCopy(nonce, 0, payload, 1, NonceSize);
        Buffer.BlockCopy(tag, 0, payload, 1 + NonceSize, TagSize);
        Buffer.BlockCopy(ciphertext, 0, payload, 1 + NonceSize + TagSize, ciphertext.Length);

        var path = PathFor(key);
        var temporaryPath = path + ".tmp";
        await File.WriteAllBytesAsync(temporaryPath, payload);
        RestrictFilePermissions(temporaryPath);
        File.Move(temporaryPath, path, overwrite: true);
    }

    public async Task<T> GetAsync<T>(string key)
    {
        var path = PathFor(key);
        if (!File.Exists(path)) return default!;
        var payload = await File.ReadAllBytesAsync(path);
        if (payload.Length < 1 + NonceSize + TagSize || payload[0] != FormatVersion)
            throw new CryptographicException("The Gmail token cache uses the legacy DPAPI format or is invalid. Delete the token cache and bootstrap OAuth again.");

        var ciphertextLength = payload.Length - 1 - NonceSize - TagSize;
        var clearBytes = new byte[ciphertextLength];
        using (var aes = new AesGcm(_encryptionKey, TagSize))
            aes.Decrypt(
                payload.AsSpan(1, NonceSize),
                payload.AsSpan(1 + NonceSize + TagSize),
                payload.AsSpan(1 + NonceSize, TagSize),
                clearBytes);
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

    private static byte[] ParseEncryptionKey(string base64EncryptionKey)
    {
        try
        {
            var key = Convert.FromBase64String(base64EncryptionKey);
            if (key.Length == 32) return key;
        }
        catch (FormatException)
        {
            // The configuration error below provides the remediation.
        }

        throw new InvalidOperationException(
            "Gmail:TokenEncryptionKey must be a Base64-encoded 32-byte key. " +
            "Generate one on macOS/Linux with `openssl rand -base64 32`.");
    }

    private static void RestrictDirectoryPermissions(string directory)
    {
        if (!OperatingSystem.IsWindows())
            File.SetUnixFileMode(directory, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
    }

    private static void RestrictFilePermissions(string path)
    {
        if (!OperatingSystem.IsWindows())
            File.SetUnixFileMode(path, UnixFileMode.UserRead | UnixFileMode.UserWrite);
    }
}
