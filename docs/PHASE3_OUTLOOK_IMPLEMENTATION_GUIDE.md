# Deprecated — Replaced by IMAP OAuth

> Xem [IMAP_OAUTH_SETUP.md](IMAP_OAUTH_SETUP.md). Microsoft Graph webhook/delta sync không còn là implementation Phase 3.

# Phase 3 — Outlook Provider Email Pipeline: Implementation Guide

## 1. Phạm vi

Phase 3 nhận email từ **một Outlook shared mailbox**, loại email không liên quan và đưa nội dung đã chuẩn hóa vào AI worker hiện có. Output là `ChangeSignal` mô tả thay đổi được nhắc tới trong email.

Không thực hiện API comparison, tạo diff, review hay cập nhật integration trong phase này.

```text
Microsoft Graph webhook
        |
        v
Outlook webhook endpoint -----> delta sync (bù notification bị mất)
        |
        v
Deduplicate -> Filter -> Normalize
        |
        v
EmailAnalysisService.QueueAsync
        |
        v
RabbitMQ: email.analysis.requested -> Python AI worker -> ChangeSignal
```

Microsoft Graph subscription chỉ gửi notification; backend phải lấy nội dung mail bằng Graph API. Delta query cung cấp incremental sync và phải lưu lại toàn bộ `@odata.deltaLink`. Tham khảo [Create subscription](https://learn.microsoft.com/en-us/graph/api/subscription-post-subscriptions?view=graph-rest-1.0) và [message delta](https://learn.microsoft.com/en-us/graph/api/message-delta?view=graph-rest-1.0).

## 2. Azure và local setup

1. Tạo **App registration** trong Microsoft Entra ID của tenant chứa shared mailbox.
2. Thêm Microsoft Graph **Application permission** `Mail.Read`, sau đó tenant administrator cấp admin consent. Với shared/delegated folder phải dùng application permission, không dùng `Mail.Read.Shared`. [Microsoft Graph subscription permissions](https://learn.microsoft.com/en-us/graph/api/subscription-post-subscriptions?view=graph-rest-1.0)
3. Tạo client secret hoặc certificate. Không commit giá trị này.
4. Tạo Dev Tunnel cho backend để có URL HTTPS public, ví dụ `https://<tunnel>.devtunnels.ms/api/outlook/webhook`.
5. Thiết lập environment variables trước khi chạy backend:

```powershell
$env:Outlook__TenantId = "<tenant-id>"
$env:Outlook__ClientId = "<application-client-id>"
$env:Outlook__ClientSecret = "<secret-value>"
$env:Outlook__SharedMailbox = "provider-notifications@company.com"
$env:Outlook__NotificationUrl = "https://<tunnel>.devtunnels.ms/api/outlook/webhook"
$env:Outlook__AllowedSenderDomains__0 = "stripe.com"
$env:Outlook__AllowedSenderDomains__1 = "twilio.com"
```

Thêm packages vào backend:

```powershell
dotnet add package Microsoft.Graph
dotnet add package Azure.Identity
dotnet add package HtmlAgilityPack
```

Ví dụ cấu hình an toàn trong `appsettings.Development.json` (file này đã được ignore):

```json
{
  "Outlook": {
    "TenantId": "",
    "ClientId": "",
    "ClientSecret": "",
    "SharedMailbox": "provider-notifications@company.com",
    "NotificationUrl": "https://<tunnel>.devtunnels.ms/api/outlook/webhook",
    "AllowedSenderDomains": ["stripe.com", "twilio.com"]
  }
}
```

## 3. Data model và registration

Tạo model lưu dấu vết ingestion. `InternetMessageId` là khóa idempotency chính; `ContentHash` là fallback khi provider không gửi ID đó.

```csharp
public sealed class OutlookMessageRecord
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string GraphMessageId { get; set; } = string.Empty;
    public string InternetMessageId { get; set; } = string.Empty;
    public string ContentHash { get; set; } = string.Empty;
    public string Sender { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string Status { get; set; } = "Received"; // Received, Ignored, Queued
    public string? IgnoreReason { get; set; }
    public DateTime ReceivedAt { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public sealed class OutlookSyncState
{
    public string Mailbox { get; set; } = string.Empty;
    public string Folder { get; set; } = "Inbox";
    public string? DeltaLink { get; set; }
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
```

Trong `IntegrationTrackingDbContext`, thêm `DbSet<OutlookMessageRecord>` và `DbSet<OutlookSyncState>`. Tạo unique index cho `InternetMessageId` (chỉ với giá trị không rỗng) và `ContentHash`; sau đó tạo EF Core migration.

Đăng ký Graph client và service trong `Program.cs`:

```csharp
builder.Services.Configure<OutlookOptions>(builder.Configuration.GetSection("Outlook"));
builder.Services.AddSingleton<TokenCredential>(sp =>
{
    var options = sp.GetRequiredService<IOptions<OutlookOptions>>().Value;
    return new ClientSecretCredential(options.TenantId, options.ClientId, options.ClientSecret);
});
builder.Services.AddSingleton(sp => new GraphServiceClient(
    sp.GetRequiredService<TokenCredential>(),
    ["https://graph.microsoft.com/.default"]));
builder.Services.AddScoped<OutlookMailService>();
builder.Services.AddScoped<ProviderEmailFilter>();
builder.Services.AddScoped<EmailNormalizer>();
builder.Services.AddHostedService<OutlookDeltaSyncWorker>();
```

## 4. Webhook và Graph subscription

Microsoft Graph gọi `GET` với `validationToken` khi tạo/gia hạn subscription. Endpoint phải trả token dạng plain text, không serialize JSON.

```csharp
[ApiController]
[Route("api/outlook/webhook")]
public sealed class OutlookWebhookController(OutlookMailService service) : ControllerBase
{
    [HttpGet]
    public IActionResult Validate([FromQuery] string? validationToken) =>
        string.IsNullOrWhiteSpace(validationToken)
            ? BadRequest()
            : Content(validationToken, "text/plain");

    [HttpPost]
    public async Task<IActionResult> Receive(
        [FromBody] GraphNotificationCollection notification,
        CancellationToken cancellationToken)
    {
        foreach (var item in notification.Value)
        {
            // Verify clientState before accepting the notification.
            await service.ProcessNotificationAsync(item, cancellationToken);
        }
        return Accepted();
    }
}

public sealed class GraphNotificationCollection
{
    public List<GraphNotification> Value { get; init; } = [];
}

public sealed class GraphNotification
{
    public string SubscriptionId { get; init; } = string.Empty;
    public string ClientState { get; init; } = string.Empty;
    public string Resource { get; init; } = string.Empty;
}
```

Tạo subscription cho Inbox của shared mailbox. `clientState` là secret random riêng, lưu trong configuration/secret store và so sánh tại webhook.

```http
POST https://graph.microsoft.com/v1.0/subscriptions
Content-Type: application/json

{
  "changeType": "created",
  "notificationUrl": "https://<tunnel>.devtunnels.ms/api/outlook/webhook",
  "resource": "/users/provider-notifications@company.com/mailFolders('Inbox')/messages",
  "expirationDateTime": "<UTC date within Graph-supported lifetime>",
  "clientState": "<random-secret>"
}
```

Backend cung cấp `POST /api/outlook/webhook/subscription` để tạo/gia hạn subscription; ID và expiry được lưu trong `OutlookSyncState`. `OutlookDeltaSyncWorker` gia hạn khi expiry còn dưới hai giờ. Không hard-code expiry duration dài hơn giới hạn resource Microsoft Graph hiện hành.

## 5. Lấy mail, deduplicate và filter

Webhook chỉ gọi `ProcessNotificationAsync`; service parse Graph message ID từ `Resource`, đọc message qua Graph, rồi chuyển sang pipeline.

```csharp
public async Task ProcessNotificationAsync(GraphNotification notification, CancellationToken ct)
{
    if (!CryptographicOperations.FixedTimeEquals(
            Encoding.UTF8.GetBytes(notification.ClientState),
            Encoding.UTF8.GetBytes(_options.ClientState)))
        throw new SecurityException("Invalid Graph clientState.");

    var messageId = ExtractMessageId(notification.Resource);
    var message = await _graph.Users[_options.SharedMailbox].Messages[messageId]
        .GetAsync(config => config.QueryParameters.Select =
            ["id", "internetMessageId", "from", "subject", "body", "receivedDateTime"]);

    if (message is not null)
        await IngestAsync(message, ct);
}
```

Hash must use stable input (`sender + subject + normalized body + received minute`), not raw HTML.

```csharp
var normalized = normalizer.Normalize(message.Body?.Content ?? string.Empty);
var key = message.InternetMessageId ?? string.Empty;
var contentHash = Convert.ToHexString(SHA256.HashData(
    Encoding.UTF8.GetBytes($"{sender}|{message.Subject}|{normalized.Text}|{receivedAt:O}")));

if (await repository.ExistsAsync(key, contentHash, ct))
    return; // already processed

var decision = filter.Evaluate(sender, message.Subject ?? "", normalized.Text);
await repository.SaveReceivedAsync(message, contentHash, decision, ct);
if (!decision.Accepted)
    return;
```

Recommended rules:

```csharp
public FilterDecision Evaluate(string sender, string subject, string text)
{
    var domain = sender.Split('@').LastOrDefault()?.ToLowerInvariant();
    if (string.IsNullOrEmpty(domain) || !_allowedDomains.Contains(domain))
        return FilterDecision.Ignore("Sender domain is not an approved provider.");
    if (Regex.IsMatch(subject, @"\b(out of office|automatic reply|delivery failed)\b", RegexOptions.IgnoreCase))
        return FilterDecision.Ignore("Automated mailbox message.");
    if (!Regex.IsMatch($"{subject} {text}", @"\b(deprecat|migration|api v\d|endpoint|webhook|rate limit|schema|oauth)\b", RegexOptions.IgnoreCase))
        return FilterDecision.Ignore("No API-change indicator.");
    return FilterDecision.Accept();
}
```

## 6. Normalize và publish vào Phase 2

Normalizer phải đưa **text sạch**, không phải raw HTML, vào AI. Có thể dùng HtmlAgilityPack, sau đó bỏ quoted reply/signature bằng rule đơn giản và tiếp tục cải thiện bằng test data thật.

```csharp
public NormalizedEmail Normalize(string html)
{
    var document = new HtmlDocument();
    document.LoadHtml(html);
    var text = HtmlEntity.DeEntitize(document.DocumentNode.InnerText);
    text = Regex.Replace(text, @"(?ms)^On .+?wrote:.*$", "");
    text = Regex.Replace(text, @"(?ms)\n--\s*\n.*$", "");
    text = Regex.Replace(text, @"\s+", " ").Trim();
    var urls = Regex.Matches(text, @"https?://[^\s)]+")
        .Select(x => x.Value).Distinct().ToList();
    return new NormalizedEmail(text, urls);
}
```

Sau filter, dùng **service Phase 2 hiện có** để record `EmailAnalysis` được tạo trước khi message được publish:

```csharp
await emailAnalysisService.QueueAsync(new AnalyzeEmailRequest
{
    EmailId = outlookRecord.Id,
    Sender = sender,
    Subject = message.Subject ?? string.Empty,
    Body = normalized.Text,
    ReceivedAt = receivedAt.UtcDateTime
}, cancellationToken);
```

Lệnh trên tạo record `Queued` rồi publish `MessageEnvelope<AnalyzeEmailRequest>` bằng routing key `email.analysis.requested`; không tạo contract RabbitMQ mới cho AI worker. Có thể publish thêm audit events `email.received` và `email.filtered`, nhưng chúng không thay thế `email.analysis.requested`.

## 7. Delta sync và recovery

`OutlookDeltaSyncWorker` chạy định kỳ (ví dụ 5 phút), dùng `OutlookSyncState.DeltaLink` nếu có. Trong initial sync, gọi:

```text
GET /users/{shared-mailbox}/mailFolders('Inbox')/messages/delta?
    $select=id,internetMessageId,from,subject,body,receivedDateTime
```

Theo toàn bộ `@odata.nextLink` đến trang cuối; lưu `@odata.deltaLink` vào database. Lần sau gọi chính URL delta link đã lưu. Bỏ entries có `@removed`, sau đó đưa từng message mới vào cùng `IngestAsync` như webhook. Delta query là đường recovery, nên idempotency phải luôn nằm trong ingestion service.

## 8. Runbook test

```powershell
# Infrastructure và Phase 2 services
docker compose up -d
cd backend; dotnet run
cd ai-service; .\.venv\Scripts\python.exe worker.py

# Expose backend HTTPS then configure the tunnel URL in Outlook:NotificationUrl.
devtunnel host -p <backend-https-port> --allow-anonymous
```

Test theo thứ tự:

1. Tạo Graph subscription và xác nhận endpoint trả chính xác `validationToken`.
2. Gửi mail từ domain allow-list với nội dung "API v2 is deprecated"; record chuyển `Received` -> `Queued`, rồi `EmailAnalysis` chuyển `Completed`.
3. Gửi lại cùng mail/internet message ID; không được tạo job AI thứ hai.
4. Gửi out-of-office, bounce và sender domain không nằm allow-list; record `Ignored` với lý do và không có message trong worker queue.
5. Gửi HTML có quoted reply/signature; xác minh AI body chỉ có phần nội dung mới.
6. Tắt webhook tạm thời, gửi mail, chạy delta sync; xác minh mail vẫn được ingest đúng một lần.

## 9. Security checklist

- Chỉ dùng environment variables, Azure Key Vault hoặc secret store cho client secret, `clientState` và connection strings.
- Verify `clientState` theo constant-time comparison trước khi process notification.
- Restrict Graph application access to mailbox được phép bằng Exchange application access policy/RBAC phù hợp tenant.
- Không log raw email body, authorization header hoặc secret; log correlation ID/message ID và filter reason.
- Không triển khai comparison, diff, approve/reject hoặc auto-update trong Phase 3.
