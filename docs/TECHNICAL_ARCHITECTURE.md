# Kiến trúc kỹ thuật — Integration Tracking

## 1. Mục tiêu hệ thống

Hệ thống nhận email thông báo từ API provider, bỏ qua email rác/không liên quan, phát hiện API change, sau đó tạo đề xuất cập nhật `actions_manifest.json` để admin review thủ công. Hệ thống **không tự ghi đè** manifest hiện hành.

```text
Gmail service mailbox
  -> Gmail API / Pub/Sub hoặc polling
  -> ASP.NET Core backend
  -> RabbitMQ
  -> Python AI worker
  -> PostgreSQL + proposal artifacts
  -> Admin review API
```

## 2. Công nghệ sử dụng

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| Backend API | ASP.NET Core / .NET 10 | REST API, Gmail ingestion, database, proposal/review, RabbitMQ consumer |
| API documentation | Swagger / Swashbuckle | Test và mô tả REST endpoint tại `/swagger` |
| ORM | Entity Framework Core 10 | Mapping PostgreSQL, EF migrations |
| Database | PostgreSQL 16 | Lưu email, trạng thái AI, Gmail checkpoint, proposal, review audit |
| Message broker | RabbitMQ 3.13 Management | Giao tiếp bất đồng bộ backend ↔ AI, retry/DLQ/audit events |
| AI service | Python 3 + FastAPI + Pydantic | Rule-based API-change detection; worker dùng `aio-pika` |
| Email | Gmail API + Google OAuth 2.0 | Đọc Gmail bằng scope `gmail.readonly` |
| Gmail notification | Google Cloud Pub/Sub | Thông báo Gmail thay đổi mailbox; polling 5 phút là fallback |
| HTML processing | HtmlAgilityPack | Chuyển body email HTML thành text để lọc/phân tích |
| Local runtime | Docker Compose | Chạy RabbitMQ và PostgreSQL |

## 3. Cấu trúc service và luồng xử lý

```text
1. Gmail API đọc email INBOX
2. Backend deduplicate theo Gmail message ID/content hash
3. ProviderEmailFilter
   ├─ sender domain không allow-list / auto reply / bounce / không có tín hiệu API change
   │  -> email_source_records.Status = Ignored
   └─ email hợp lệ
      -> EmailNormalizer
      -> email.analysis.requested
4. Python worker nhận request, tạo ChangeSignal
5. Backend nhận email.analysis.completed
   -> email_analyses = Completed
   -> provider.update.detected
   -> tạo TemplateProposal nếu provider/integration map rõ ràng
6. Admin gọi Review API để xem proposal, diff và approve/reject/regenerate
```

### Gmail nhận mail

`GmailIngestionWorker` hoạt động theo hai cơ chế:

- **Pub/Sub push:** Gmail `watch` publish event vào Google Cloud Pub/Sub. Subscription phải là loại **Push**, có endpoint HTTPS công khai: `https://<domain>/api/gmail/push`.
- **Polling fallback:** backend gọi Gmail `history.list` theo checkpoint `HistoryId` mỗi 5 phút. Vì vậy local vẫn nhận email khi không có public HTTPS endpoint, nhưng có độ trễ tối đa khoảng 5 phút.

`POST /api/gmail/push` chỉ đánh thức worker để sync ngay. Lệnh `Invoke-RestMethod` với payload `{}` là mô phỏng callback local, không phải quy trình bắt buộc ở production.

## 4. Thiết kế PostgreSQL

### `email_analyses`

Lưu trạng thái xử lý AI cho mỗi email.

| Cột | Ý nghĩa |
|---|---|
| `EmailId` (PK) | Correlation ID xuyên suốt RabbitMQ workflow |
| `Sender`, `Subject`, `Body`, `ReceivedAt` | Dữ liệu email đã normalize gửi cho AI |
| `Status` | `Queued`, `Completed`, `Failed` |
| `ResultJson` | `ChangeSignal` ở dạng `jsonb` |
| `ErrorMessage`, `CreatedAt`, `UpdatedAt` | Lỗi và audit thời gian |

### `email_source_records`

Audit email nhận từ Gmail trước và sau filtering.

| Cột | Ý nghĩa |
|---|---|
| `Id` (PK) | ID nội bộ, dùng làm `EmailId` khi gửi AI |
| `Mailbox`, `Folder` | Mailbox và folder nguồn, hiện là `INBOX` |
| `GmailMessageId`, `GmailThreadId` | Identity của Gmail message/thread |
| `InternetMessageId`, `ContentHash` | Dedupe/audit bổ sung |
| `Sender`, `Subject`, `ReceivedAt` | Metadata email |
| `Status` | `Received`, `Ignored`, `Queued` |
| `IgnoreReason` | Lý do lọc bỏ mail |
| `EmailAnalysisId` | Liên kết logic tới `email_analyses` |

Ràng buộc idempotency:

- Unique: `Mailbox + GmailMessageId`.
- Unique fallback: `ContentHash`.

### `gmail_sync_states`

Lưu checkpoint Gmail để không bỏ sót email khi Pub/Sub bị trễ/mất.

| Cột | Ý nghĩa |
|---|---|
| `Mailbox`, `Folder` (composite PK) | Mailbox đang được đồng bộ |
| `HistoryId` | Gmail history checkpoint |
| `WatchExpiresAt` | Thời gian Gmail watch hết hạn, backend gia hạn trước hạn |
| `UpdatedAt` | Lần sync thành công gần nhất |

### `template_proposals`

Lưu đề xuất thay đổi integration. Một email chỉ có một proposal cho một integration.

| Cột | Ý nghĩa |
|---|---|
| `Id` (PK) | Proposal ID |
| `EmailId`, `Provider`, `IntegrationId` | Nguồn change và integration liên quan |
| `BaseManifestHash` | Hash manifest gốc dùng để tạo diff |
| `Status` | `Pending`, `NeedsReview`, `Approved`, `Rejected`, `Failed` |
| `ArtifactDirectory` | Thư mục artifact: manifest mới, changelog, diff, evidence |
| `EvidenceJson`, `ErrorMessage` | Evidence/lỗi generation |
| `CreatedAt`, `UpdatedAt` | Audit |

Unique: `EmailId + IntegrationId`.

### `review_decisions`

Audit quyết định admin. `Approve` chỉ lưu quyết định, không tự apply proposal.

| Cột | Ý nghĩa |
|---|---|
| `Id` (PK) | Review decision ID |
| `ProposalId` | Proposal được review |
| `Decision` | `Approved`, `Rejected`, hoặc `Regenerate` |
| `AdminIdentity`, `Note`, `CreatedAt` | Người review, ghi chú và thời điểm |

## 5. Thiết kế RabbitMQ

### Exchanges

| Exchange | Type | Mục đích |
|---|---|---|
| `integration-tracking.events` | Durable topic | Event nghiệp vụ chính |
| `integration-tracking.retry` | Durable direct | Đưa request vào retry queue theo delay |

### Routing keys và queues

| Routing key | Producer | Queue/consumer | Mục đích |
|---|---|---|---|
| `email.received` | Gmail backend | Audit event | Email đã được lưu/dedupe |
| `email.filtered` | Gmail backend | Audit event | Email vượt qua filter |
| `email.analysis.requested` | Backend | `email.analysis.worker` / Python worker | Yêu cầu AI phân tích email |
| `email.analysis.completed` | Python worker | `email.analysis.backend` | Trả `ChangeSignal` thành công |
| `email.analysis.failed` | Python worker | `email.analysis.backend` | Báo thất bại sau retry |
| `email.analysis.dlq` | Python worker | `email.analysis.dlq` | Lưu message không xử lý được |
| `provider.update.detected` | Backend | `provider.update.handoff` | Handoff provider update cho downstream |
| `integration.update.proposed` | Backend | `integration.update.proposed` | Báo proposal đã tạo |
| `integration.update.reviewed` | Backend | `integration.update.reviewed` | Báo admin review đã quyết định |

### Envelope message

Mọi message dùng JSON envelope versioned:

```json
{
  "version": 1,
  "messageId": "uuid-or-random-id",
  "correlationId": "email-id",
  "occurredAtUtc": "2026-08-19T14:00:00Z",
  "payload": {}
}
```

`correlationId` là `EmailId`, giúp trace một email xuyên suốt Gmail → backend → RabbitMQ → Python worker → PostgreSQL.

### Retry và DLQ

Python worker dùng manual acknowledgement và `prefetch_count = 1`.

```text
Worker lỗi lần 1 -> email.analysis.retry.10s
Worker lỗi lần 2 -> email.analysis.retry.30s
Worker lỗi lần 3 -> email.analysis.retry.60s
Lỗi tiếp       -> email.analysis.failed + email.analysis.dlq
```

Retry queues có TTL và dead-letter message quay lại `email.analysis.requested` để worker xử lý lại.

## 6. Template và Admin Review

Provider/integration mapping được khai báo ở:

```text
backend/Configuration/provider-integrations.json
```

Mỗi integration có một `actions_manifest.json`, gồm tối thiểu:

```json
{
  "base_url": "https://api.provider.com",
  "auth": { "type": "bearer" },
  "actions": []
}
```

Khi LLM proposal được cấu hình, artifacts được ghi tại:

```text
backend/proposals/<proposal-id>/
  ├─ actions_manifest.json
  ├─ CHANGELOG.md
  ├─ diff.patch
  └─ evidence.json
```

Review endpoints:

```text
GET  /api/reviews
GET  /api/reviews/{id}
POST /api/reviews/{id}/approve
POST /api/reviews/{id}/reject
POST /api/reviews/{id}/regenerate
```

## 7. Local ports và vận hành

| Service | URL/port |
|---|---|
| Backend | `http://localhost:5000` |
| Swagger | `http://localhost:5000/swagger` |
| RabbitMQ AMQP | `localhost:5672` |
| RabbitMQ Management | `http://localhost:15672` |
| PostgreSQL | `localhost:5434` |

Docker credentials local:

```text
RabbitMQ: integration_tracking / integration_tracking
PostgreSQL: integration_tracking / integration_tracking
Database: integration_tracking
```

Không commit Gmail OAuth client secret, Gmail token cache, LLM API key hoặc production database credentials. Xem [GMAIL_PROVIDER_PIPELINE_SETUP.md](GMAIL_PROVIDER_PIPELINE_SETUP.md) để cấu hình Gmail.
