# ProviderUpdateEvent Contract

Đây là output bàn giao của capability A/B cho team documentation, diff, impact analysis và admin review.

RabbitMQ:

```text
Exchange: integration-tracking.events (topic, durable)
Routing key: provider.update.detected
Queue: provider.update.handoff (durable)
Correlation ID: emailId
```

Payload trong `MessageEnvelope<ProviderUpdateEvent>`:

```json
{
  "eventId": "email-id-stable-for-idempotency",
  "emailId": "email-id",
  "provider": "stripe.com",
  "source": {
    "sender": "updates@stripe.com",
    "subject": "API v1 deprecation notice",
    "receivedAt": "2026-08-18T00:00:00Z"
  },
  "changeTypes": ["DEPRECATION", "VERSION_CHANGE"],
  "summary": "Potential API change detected.",
  "confidence": 0.7,
  "evidence": {
    "matchedTerms": ["deprecated", "api v2", "migration"],
    "urls": []
  },
  "detectedAt": "2026-08-18T00:01:00Z"
}
```

Consumer phía downstream phải dùng `eventId`/`emailId` để xử lý idempotently. Event chỉ được publish khi `changeDetected=true`; email không có thay đổi vẫn có `ChangeSignal` trong API/database nhưng không tạo handoff event.
