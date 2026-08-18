# Phase 3 — IMAP Email Ingestion & Change Signal Extraction

## Mục tiêu

Phase 3 nhận email thông báo từ API provider qua một Microsoft 365 service mailbox, lọc mail không liên quan, chuẩn hóa nội dung và gửi email hợp lệ đến AI. Kết quả là `ChangeSignal` và `ProviderUpdateEvent` cho đội xử lý capability C/D/E.

Phase này không tải documentation, không so sánh API hoặc integration, không tạo diff và không có admin approval.

## Pipeline

```text
Microsoft 365 service mailbox
        |
        v
IMAP OAuth (XOAUTH2) — IDLE, polling fallback 5 phút
        |
        v
UID checkpoint + deduplicate
        |
        +--> email.received
        v
Provider filter (allow-list, spam, auto-reply, bounce, newsletter)
        |
        +--> Ignored + lý do, hoặc email.filtered
        v
HTML/text normalization (footer, signature, quoted reply, URLs)
        |
        v
email.analysis.requested (RabbitMQ)
        |
        v
AI worker -> ChangeSignal
        |
        v
email.analysis.completed -> PostgreSQL
        |
        v
provider.update.detected -> provider.update.handoff
```

## IMAP OAuth

- Dùng user mailbox riêng, không phải shared mailbox.
- Dùng delegated OAuth scope `IMAP.AccessAsUser.All` với device-code login và MSAL cache mã hóa DPAPI trên Windows.
- Không dùng Microsoft Graph, `Mail.Read`, webhook, delta sync, client secret, Basic Auth hay app password.
- Mailbox được mở `ReadOnly`; pipeline không đánh dấu Seen và không di chuyển email.
- Nếu IDLE mất kết nối, worker reconnect và quét lại UID lớn hơn checkpoint. `UIDVALIDITY` thay đổi sẽ reset checkpoint.

Xem hướng dẫn đăng ký app và chạy local tại [IMAP_OAUTH_SETUP.md](IMAP_OAUTH_SETUP.md).

## Lưu trữ và idempotency

- `imap_sync_states`: mailbox, folder, `UIDVALIDITY`, UID checkpoint và thời điểm sync.
- `email_source_records`: mailbox, folder, UIDVALIDITY, UID, internet message ID, content hash, status và lý do bỏ qua.
- Khóa chính chống trùng là `mailbox + folder + UIDVALIDITY + UID`; content hash là fallback cho email bị copy hoặc reconnect.
- Chỉ email qua filter mới được đưa vào AI. Email bị lọc có status `Ignored` để audit.

## Event contracts

Mọi event dùng `MessageEnvelope` với `messageId`, `correlationId`, `occurredAtUtc` và `payload`.

| Event | Ý nghĩa |
|---|---|
| `email.received` | Email mới đã được lưu và deduplicate. |
| `email.filtered` | Email vượt qua provider/rule filter. |
| `email.analysis.requested` | Nội dung đã chuẩn hóa chờ AI phân tích. |
| `email.analysis.completed` | AI trả `ChangeSignal`. |
| `provider.update.detected` | Backend tạo handoff event cho đội downstream. |

## Definition of Done

- IMAP OAuth đọc được email mới và không thay đổi trạng thái email trong INBOX.
- Reconnect/polling không xử lý trùng email.
- Email rác hoặc ngoài allow-list được lưu `Ignored`, không gửi AI.
- Email hợp lệ đi hết RabbitMQ → AI → `Completed` → `provider.update.handoff`.
