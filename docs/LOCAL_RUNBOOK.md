# Hướng dẫn chạy local và cấu hình keys

Tài liệu này hướng dẫn chạy toàn bộ pipeline local:

```text
Gmail -> Backend -> RabbitMQ -> Python AI worker -> PostgreSQL -> Review API
```

## 1. Yêu cầu trước khi chạy

- .NET SDK 10
- Python 3.11+ và virtual environment tại `ai-service/.venv`
- Docker Desktop đang chạy
- Gmail service mailbox
- Google Cloud project đã bật Gmail API và Cloud Pub/Sub API

## 2. Các keys và configuration cần có

Không commit secret vào `backend/appsettings.json`. Dùng biến môi trường trong terminal chạy backend hoặc secret store.

### Cách lưu local secrets an toàn hơn

Backend đã bật **.NET User Secrets**. Secrets được lưu ngoài repository và không xuất hiện trong Git. Chạy các lệnh này một lần, thay placeholder bằng giá trị thật:

```powershell
cd C:\Users\hoang\Downloads\Integration_Tracking_Update\backend

dotnet user-secrets set "Gmail:ClientId" "<google-oauth-client-id>"
dotnet user-secrets set "Gmail:ClientSecret" "<google-oauth-client-secret>"
dotnet user-secrets set "Gmail:ServiceMailbox" "provider-notifications@gmail.com"
dotnet user-secrets set "Gmail:PubSubTopic" "projects/<project-id>/topics/gmail-provider-updates"
dotnet user-secrets set "Gmail:AllowedSenderDomains:0" "gmail.com"
dotnet user-secrets set "ProposalLlm:ApiKey" "<llm-api-key>"
dotnet user-secrets set "ProposalLlm:Model" "<model-name>"
```

Không dán output của `dotnet user-secrets list` vào chat hoặc Git. Khi deploy production, dùng secret store của platform (ví dụ Google Secret Manager/Azure Key Vault), không dùng User Secrets.

| Biến môi trường | Bắt buộc | Giá trị lấy từ đâu |
|---|---:|---|
| `Gmail__ClientId` | Có | Google Cloud → Google Auth Platform → Clients → OAuth Desktop Client |
| `Gmail__ClientSecret` | Có | OAuth Desktop Client ở Google Cloud |
| `Gmail__ServiceMailbox` | Có | Gmail chuyên nhận provider notification, ví dụ `provider-notifications@gmail.com` |
| `Gmail__PubSubTopic` | Có | `projects/<project-id>/topics/<topic-id>` |
| `Gmail__AllowedSenderDomains__0` | Có | Domain provider đầu tiên, ví dụ `stripe.com`; khi test Gmail dùng `gmail.com` |
| `Gmail__AllowedSenderDomains__1` | Không | Domain provider thứ hai |
| `ProposalLlm__ApiKey` | Cần để tạo proposal/diff | API key LLM compatible với endpoint đã cấu hình |
| `ProposalLlm__Model` | Cần để tạo proposal/diff | Tên model hỗ trợ JSON structured output |
| `ProposalLlm__Endpoint` | Không | Mặc định là endpoint OpenAI-compatible trong `appsettings.json` |

Các giá trị local mặc định đã có trong `backend/appsettings.json`:

```text
PostgreSQL: localhost:5434 / integration_tracking
RabbitMQ: localhost:5672 / integration_tracking
RabbitMQ UI: http://localhost:15672
Backend: http://localhost:5000
```

## 3. Chuẩn bị Google Cloud

1. Tạo/chọn Google Cloud project.
2. Bật **Gmail API** và **Cloud Pub/Sub API**.
3. Trong **Google Auth Platform**:
   - cấu hình Branding/Audience;
   - nếu dùng Gmail cá nhân, chọn `External` và thêm service mailbox vào **Test users**;
   - tạo OAuth client loại **Desktop app**;
   - copy Client ID và Client secret.
4. Tạo Pub/Sub topic, ví dụ `gmail-provider-updates`.
5. Thêm principal dưới đây vào **Permissions của Topic** với role **Pub/Sub Publisher**:

```text
gmail-api-push@system.gserviceaccount.com
```

> Role phải đặt trên **Topic**, không phải chỉ trên Subscription.

## 4. Khởi động services

### Terminal 1 — Docker

```powershell
cd C:\Users\hoang\Downloads\Integration_Tracking_Update
docker compose up -d
docker compose ps
```

Hai containers `postgres` và `rabbitmq` phải có trạng thái `Up`.

### Terminal 2 — Backend

Thay toàn bộ placeholder trước khi chạy:

```powershell
cd C:\Users\hoang\Downloads\Integration_Tracking_Update\backend

$env:Gmail__ClientId = "<google-oauth-client-id>"
$env:Gmail__ClientSecret = "<google-oauth-client-secret>"
$env:Gmail__ServiceMailbox = "provider-notifications@gmail.com"
$env:Gmail__PubSubTopic = "projects/<project-id>/topics/gmail-provider-updates"
$env:Gmail__AllowedSenderDomains__0 = "gmail.com"

# Chỉ bắt buộc khi test generate proposal/diff.
$env:ProposalLlm__ApiKey = "<llm-api-key>"
$env:ProposalLlm__Model = "<model-name>"

dotnet run --urls "http://localhost:5000"
```

Chờ log:

```text
Now listening on: http://localhost:5000
```

Kiểm tra health:

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/health"
```

### Terminal 3 — Gmail OAuth bootstrap

Chỉ thực hiện khi kết nối một Gmail mới hoặc refresh token bị mất:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/gmail/oauth/bootstrap"
```

Trình duyệt mở ra: đăng nhập đúng `Gmail__ServiceMailbox` và chọn **Allow**. Token cache local được mã hóa Windows DPAPI tại:

```text
%LOCALAPPDATA%\IntegrationTracking\gmail
```

### Terminal 4 — Python AI worker

```powershell
cd C:\Users\hoang\Downloads\Integration_Tracking_Update\ai-service
.\.venv\Scripts\python.exe worker.py
```

Chỉ chạy **một** AI worker. Log đúng:

```text
RabbitMQ analysis worker started.
```

## 5. Provider registry và action manifest

Sửa `backend/Configuration/provider-integrations.json`. Ví dụ test:

```json
{
  "providers": [
    {
      "provider": "demo-provider",
      "senderDomains": ["gmail.com"],
      "documentationDomains": ["developers.google.com"],
      "integrations": [
        {
          "id": "demo-integration",
          "manifestPath": "integrations/demo-integration/actions_manifest.json"
        }
      ]
    }
  ]
}
```

Tạo file `integrations/demo-integration/actions_manifest.json`:

```json
{
  "base_url": "https://api.example.com/v1",
  "auth": { "type": "bearer" },
  "actions": [
    {
      "name": "get-customer",
      "method": "GET",
      "path": "/customers/{id}",
      "fields": []
    }
  ]
}
```

Restart backend sau khi thay đổi biến môi trường hoặc registry.

## 6. Test email

Gửi email mới từ sender thuộc allow-list vào Gmail service mailbox.

```text
Subject: API v2 deprecation notice — action required

The endpoint https://api.example.com/v1/customers will be deprecated.
Please migrate to API v2 before 2026-12-31.

Documentation:
https://developers.google.com/gmail/api/guides/push
```

### Local: trigger sync ngay

Polling fallback chạy mỗi 5 phút. Để test không phải chờ, gọi một lần:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:5000/api/gmail/push" `
  -ContentType "application/json" `
  -Body '{"message":{"data":"e30="}}'
```

Payload `{}` chỉ mô phỏng notification local. Production không dùng lệnh này.

Kỳ vọng backend log:

```text
Queued Gmail message ... for AI analysis
Analysis ... completed
```

Kỳ vọng Python log:

```text
Completed analysis for <email-id>
```

## 7. Kiểm tra kết quả

### Swagger và RabbitMQ

```text
Swagger: http://localhost:5000/swagger
RabbitMQ Management: http://localhost:15672
User/password: integration_tracking / integration_tracking
```

### PostgreSQL

```powershell
cd C:\Users\hoang\Downloads\Integration_Tracking_Update

docker compose exec postgres psql -U integration_tracking -d integration_tracking -c 'TABLE email_source_records;'
docker compose exec postgres psql -U integration_tracking -d integration_tracking -c 'TABLE email_analyses;'
docker compose exec postgres psql -U integration_tracking -d integration_tracking -c 'TABLE template_proposals;'
```

### Review API

```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/reviews"
```

Nếu LLM key/model chưa cấu hình, Gmail → filter → AI vẫn chạy; proposal có thể là `NeedsReview` thay vì sinh artifact hoàn chỉnh.

## 8. Pub/Sub automation

Để Google tự gọi backend ngay khi có mail, subscription phải là **Push** và endpoint phải là HTTPS công khai:

```text
https://<public-domain>/api/gmail/push
```

Google Cloud không gọi được `http://localhost:5000`. Khi local, dùng polling fallback hoặc public tunnel. Nếu subscription là **Pull**, code hiện tại không tự consume Pub/Sub subscription; cần đổi sang Push hoặc bổ sung Pull consumer.

## 9. Dừng services

Nhấn `Ctrl+C` tại backend và AI worker. Dừng Docker khi cần:

```powershell
cd C:\Users\hoang\Downloads\Integration_Tracking_Update
docker compose down
```

`docker compose down` giữ volumes/database. Không chạy `docker compose down -v` nếu chưa muốn xóa dữ liệu local.
