# IMAP OAuth Setup — Microsoft 365 Service Mailbox

Phase 3 dùng IMAP OAuth 2.0 để đọc mailbox chuyên nhận email provider. Không dùng Microsoft Graph `Mail.Read`, client secret, password hay app password.

## 1. Chuẩn bị mailbox

Tạo một **user mailbox** riêng, ví dụ `provider-notifications@company.com`. Đây không phải shared mailbox; tài khoản cần có thể đăng nhập Microsoft 365 để hoàn tất device-code OAuth lần đầu.

Provider notifications phải được đăng ký gửi trực tiếp đến mailbox này.

## 2. Tạo Entra App Registration

1. Mở Microsoft Entra admin center → **App registrations** → **New registration**.
2. Chọn **Accounts in this organizational directory only**.
3. Tại **Authentication**, bật **Allow public client flows**.
4. Tại **API permissions** → **Add a permission** → **APIs my organization uses** → tìm **Office 365 Exchange Online**.
5. Chọn **Delegated permissions** và thêm `IMAP.AccessAsUser.All`.
6. Thêm `offline_access` nếu tenant hiển thị scope này trong consent; MSAL yêu cầu scope này để refresh token cache.

Copy hai ID từ trang Overview:

```powershell
$env:Imap__TenantId = "<Directory-tenant-ID>"
$env:Imap__ClientId = "<Application-client-ID>"
```

Không tạo client secret. IMAP OAuth ở project này dùng public-client device-code flow.

## 3. Cấu hình backend

Trong cùng terminal chạy backend:

```powershell
$env:Imap__TenantId = "<tenant-id>"
$env:Imap__ClientId = "<client-id>"
$env:Imap__ServiceMailbox = "provider-notifications@company.com"
$env:Imap__Host = "outlook.office365.com"
$env:Imap__Port = "993"
$env:Imap__Folder = "INBOX"
$env:Imap__AllowedSenderDomains__0 = "stripe.com"
$env:Imap__AllowedSenderDomains__1 = "twilio.com"

dotnet run
```

MSAL lưu token encrypted bằng Windows DPAPI vào `%LOCALAPPDATA%\IntegrationTracking\imap-msal.cache`. Không commit file cache này.

## 4. Device-code login lần đầu

Khi backend đang chạy, gọi:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5000/api/imap/oauth/bootstrap"
```

Backend log sẽ hiển thị Microsoft login URL và device code. Đăng nhập bằng **service mailbox account**, nhập code rồi approve consent. Khi request trả `authenticated`, token cache đã sẵn sàng; worker IMAP tự kết nối và tiếp tục refresh token silent.

Nếu consent bị tenant chặn, gửi IT administrator yêu cầu duyệt **delegated** `IMAP.AccessAsUser.All` cho app registration. Đây không phải `Mail.Read` application permission.

## 5. Chạy pipeline

```powershell
# Terminal 1
docker compose up -d

# Terminal 2
cd backend
dotnet run

# Terminal 3
cd ai-service
.\.venv\Scripts\python.exe worker.py
```

Luồng hoạt động:

```text
IMAP INBOX (read-only) -> filter/normalize -> RabbitMQ -> AI worker
-> provider.update.detected -> provider.update.handoff
```

Worker dùng IMAP IDLE, tự reconnect định kỳ và quét UID checkpoint để không bỏ lỡ mail khi mất kết nối. Mail không bị mark-as-read hoặc move.

## 6. Security

- Exchange Online Basic Auth/app passwords không được dùng.
- Giới hạn quyền app chỉ ở delegated `IMAP.AccessAsUser.All` và service mailbox riêng.
- Không copy encrypted MSAL cache sang source control hay chia sẻ giữa người dùng/máy.
- Production phải chuyển token cache vào managed secret store thay vì Windows local profile.
