# Deprecated — Replaced by IMAP OAuth

> Không dùng tài liệu này cho implementation hiện tại. Xem [IMAP_OAUTH_SETUP.md](IMAP_OAUTH_SETUP.md). Microsoft Graph Mail API đã được thay bằng IMAP OAuth.

# Đăng ký Microsoft Entra App và lấy Outlook/Graph keys

Tài liệu này tạo credentials cho Phase 3 đọc **shared mailbox** của Outlook qua Microsoft Graph. Không dùng mật khẩu mailbox và không commit secret vào Git.

## 1. Điều kiện cần

- Tài khoản có quyền tạo App registration trong Microsoft Entra tenant.
- Tenant administrator có quyền **Grant admin consent**.
- Shared mailbox đã tồn tại, ví dụ `provider-notifications@company.com`.
- Backend chạy local và có public HTTPS URL qua Dev Tunnel để nhận webhook.

## 2. Tạo App registration

1. Vào [Microsoft Entra admin center](https://entra.microsoft.com/).
2. Chọn **Identity** → **Applications** → **App registrations** → **New registration**.
3. Đặt tên, ví dụ `integration-tracking-outlook`.
4. Chọn **Accounts in this organizational directory only**.
5. Không cần Redirect URI vì backend dùng application authentication, sau đó chọn **Register**.

Sau khi tạo, tại trang **Overview**, copy hai giá trị:

| Environment variable | Lấy ở đâu |
|---|---|
| `Outlook__ClientId` | **Application (client) ID** |
| `Outlook__TenantId` | **Directory (tenant) ID** |

## 3. Tạo client secret

1. Trong App registration, chọn **Certificates & secrets**.
2. Chọn **New client secret**.
3. Nhập description, ví dụ `integration-tracking-local` và chọn expiry ngắn phù hợp môi trường local.
4. Chọn **Add**.
5. Copy ngay trường **Value**; giá trị này chỉ xuất hiện một lần.

Lưu thành environment variable:

```powershell
$env:Outlook__ClientSecret = "<client-secret-VALUE>"
```

Không dùng trường **Secret ID**; backend cần **Value**.

## 4. Cấp Microsoft Graph permission

1. Chọn **API permissions** → **Add a permission** → **Microsoft Graph**.
2. Chọn **Application permissions**.
3. Tìm và thêm `Mail.Read`.
4. Chọn **Grant admin consent for <tenant>** và xác nhận status là **Granted**.

`Mail.Read` application permission là cần thiết để đọc mail và tạo subscription cho shared/delegated mailbox. Nếu tenant yêu cầu hạn chế phạm vi app, Exchange administrator phải cấu hình application access policy hoặc Exchange RBAC để app chỉ có thể truy cập mailbox đã chỉ định.

## 5. Chuẩn bị shared mailbox

1. Exchange/Microsoft 365 administrator tạo shared mailbox chuyên nhận notification provider.
2. Ghi lại primary SMTP address, ví dụ `provider-notifications@company.com`.
3. Không cần đăng nhập bằng mật khẩu mailbox; app dùng client credentials đã tạo ở bước trên.

```powershell
$env:Outlook__SharedMailbox = "provider-notifications@company.com"
```

## 6. Tạo webhook URL bằng Dev Tunnel

Microsoft Graph chỉ gọi endpoint HTTPS công khai. Khi backend chạy local, mở backend bằng HTTPS và host port đó bằng Dev Tunnel.

```powershell
# Terminal 1: chạy backend và xem HTTPS port được hiển thị.
cd backend
dotnet run

# Terminal 2: thay 7xxx bằng HTTPS port của backend.
devtunnel host -p 7xxx --allow-anonymous
```

Copy public URL Dev Tunnel và thêm đường dẫn webhook:

```powershell
$env:Outlook__NotificationUrl = "https://<your-tunnel>.devtunnels.ms/api/outlook/webhook"
```

> Nếu lệnh `devtunnel` chưa tồn tại, cài Microsoft dev tunnels CLI theo tài liệu nội bộ/Visual Studio của bạn, hoặc dùng một HTTPS tunnel được tổ chức phê duyệt. Production phải dùng domain HTTPS riêng, không dùng Dev Tunnel.

## 7. Tạo client state

`clientState` là secret dùng để backend xác minh notification đến từ subscription của chính app. Tạo một chuỗi ngẫu nhiên, ví dụ:

```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$env:Outlook__ClientState = [Convert]::ToHexString($bytes)
```

## 8. Cấu hình allow-list provider

Chỉ mail từ các domain này mới có thể đi tới AI. Ví dụ:

```powershell
$env:Outlook__AllowedSenderDomains__0 = "stripe.com"
$env:Outlook__AllowedSenderDomains__1 = "twilio.com"
```

## 9. Kiểm tra cấu hình local

Chạy các lệnh trong **cùng terminal** trước khi chạy backend, vì `$env:` chỉ áp dụng cho terminal hiện tại:

```powershell
$env:Outlook__TenantId = "<tenant-id>"
$env:Outlook__ClientId = "<client-id>"
$env:Outlook__ClientSecret = "<secret-value>"
$env:Outlook__SharedMailbox = "provider-notifications@company.com"
$env:Outlook__NotificationUrl = "https://<your-tunnel>.devtunnels.ms/api/outlook/webhook"
$env:Outlook__ClientState = "<random-client-state>"
$env:Outlook__AllowedSenderDomains__0 = "stripe.com"

dotnet run
```

Sau khi backend chạy, tạo subscription bằng endpoint backend:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5000/api/outlook/webhook/subscription"
```

Backend lưu subscription ID/expiry trong PostgreSQL và tự gia hạn khi còn dưới hai giờ. Microsoft Graph sẽ gọi `GET /api/outlook/webhook?validationToken=...`; endpoint cần trả nguyên token plain text mới tạo được subscription.

## 10. Bảo mật và rotation

- Không đưa `ClientSecret` hoặc `ClientState` vào `appsettings.json`, screenshot, commit hoặc chat log.
- Local: dùng terminal environment variables hoặc `appsettings.Development.json` đã được `.gitignore`.
- Production: dùng Azure Key Vault/secret store; dùng certificate thay client secret nếu tổ chức yêu cầu.
- Rotate secret trước expiry và cập nhật deployment secret trước khi vô hiệu secret cũ.
- Nếu lộ secret: revoke ngay tại **Certificates & secrets**, tạo secret mới và cập nhật environment/deployment.
