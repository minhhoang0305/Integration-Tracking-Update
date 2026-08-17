# Integration Tracking - Development Phases

## Overview

Tài liệu này dùng để theo dõi quá trình phát triển Integration Tracking.

Luồng mục tiêu cuối cùng:

```text
Provider Notification
        ↓
Email Detection
        ↓
API Change Extraction
        ↓
Provider Identification
        ↓
Official Documentation Verification
        ↓
API Difference Detection
        ↓
Integration Impact Analysis
        ↓
Generate Proposed Update
        ↓
Admin Review
        ↓
Approve / Reject
```

---

# Phase 1 - Base Communication

**Status: IN PROGRESS**

## Goal

Xây dựng communication cơ bản giữa ASP.NET Core và Python.

```text
ASP.NET Core
      ↓
HTTP REST
      ↓
FastAPI
```

## Tasks

* [x] Xác định architecture C# + Python
* [x] Xác định responsibility của từng service
* [x] Define `AnalyzeEmailRequest`
* [x] Define `ChangeSignal`
* [x] Define `IEmailAnalyzer`
* [x] Thiết kế `PythonAnalyzerClient`
* [x] Thiết kế `EmailAnalysisService`
* [x] Thiết kế FastAPI `/analyze`
* [x] Thiết kế basic Rule Detector
* [ ] Implement source code
* [ ] Run Python service
* [ ] Run ASP.NET Core service
* [ ] Test C# → Python
* [ ] Test Python → C#
* [ ] Test complete end-to-end flow
* [ ] Add error handling
* [ ] Add logging

## Definition of Done

Phase 1 hoàn thành khi request:

```text
POST /api/emails/analyze
```

có thể chạy:

```text
Client
 ↓
ASP.NET Core
 ↓
Python
 ↓
Analyze
 ↓
ASP.NET Core
 ↓
Client
```

và trả về `ChangeSignal` đúng contract.

---

# Phase 2 - RabbitMQ Communication

**Status: NOT STARTED**

## Goal

Thay communication synchronous REST bằng asynchronous messaging.

```text
ASP.NET Core
      ↓
RabbitMQ
      ↓
Python Worker
```

## Tasks

* [ ] Add RabbitMQ
* [ ] Dockerize RabbitMQ
* [ ] Define exchange
* [ ] Define queue
* [ ] Define routing keys
* [ ] Define message contract
* [ ] Implement C# Publisher
* [ ] Implement Python Consumer
* [ ] Implement result event
* [ ] Implement retry
* [ ] Implement Dead Letter Queue
* [ ] Add Correlation ID
* [ ] Add Idempotency handling
* [ ] Test message processing

## Proposed Events

```text
email.analysis.requested
email.analysis.completed
email.analysis.failed
```

## Target Flow

```text
ASP.NET Core
      ↓
email.analysis.requested
      ↓
RabbitMQ
      ↓
Python Worker
      ↓
Analyze Email
      ↓
email.analysis.completed
      ↓
RabbitMQ
      ↓
ASP.NET Core
```

---

# Phase 3 - Email Processing

**Status: NOT STARTED**

## Goal

Chuẩn hóa email trước khi đưa vào detection engine.

## Tasks

* [ ] HTML → Text
* [ ] Remove signatures
* [ ] Remove footer
* [ ] Remove quoted replies
* [ ] Extract URLs
* [ ] Extract sender domain
* [ ] Normalize subject
* [ ] Detect provider
* [ ] Handle malformed email

Output:

```text
Raw Email
   ↓
Email Cleaner
   ↓
Normalized Email
```

---

# Phase 4 - API Change Detection

**Status: NOT STARTED**

## Goal

Xác định email có chứa API change hay không.

## Detection Strategy

```text
Normalized Email
      ↓
Rule Detector
      ↓
Potential API Change?
   ┌──────┴──────┐
   No            Yes
   ↓              ↓
 Ignore      LLM Extractor
```

## Tasks

* [ ] Improve Rule Detector
* [ ] Define API change taxonomy
* [ ] Add LLM provider
* [ ] Create extraction prompt
* [ ] Structured JSON output
* [ ] Confidence scoring
* [ ] False-positive handling
* [ ] Manual review threshold

## Change Types

```text
VERSION_CHANGE
ENDPOINT_ADDED
ENDPOINT_UPDATED
ENDPOINT_REMOVED

REQUEST_SCHEMA_CHANGE
RESPONSE_SCHEMA_CHANGE

AUTH_CHANGE
SCOPE_CHANGE

RATE_LIMIT_CHANGE

DEPRECATION
SERVICE_SHUTDOWN

SDK_CHANGE
WEBHOOK_CHANGE

DOCUMENTATION_ONLY
```

---

# Phase 5 - Provider Resolution

**Status: NOT STARTED**

## Goal

Map email/change event với Integration Provider tương ứng.

Example:

```text
developer@stripe.com
        ↓
Sender domain
        ↓
stripe.com
        ↓
Provider
        ↓
Stripe Integration
```

## Tasks

* [ ] Provider model
* [ ] Provider domain mapping
* [ ] Documentation URL mapping
* [ ] Integration mapping
* [ ] Unknown provider handling

---

# Phase 6 - Documentation Verification

**Status: NOT STARTED**

## Goal

Email chỉ là signal.

Mọi API change quan trọng phải được verify lại bằng official documentation.

```text
ChangeSignal
      ↓
Provider
      ↓
Official Docs
      ↓
Verify Change
```

## Sources

Ưu tiên:

```text
1. Official OpenAPI
2. Official Swagger
3. Official API reference
4. Official changelog
5. Official migration guide
6. Official SDK
7. Documentation crawl
```

## Tasks

* [ ] Documentation fetcher
* [ ] OpenAPI discovery
* [ ] Swagger parser
* [ ] Changelog parser
* [ ] Documentation crawler
* [ ] Documentation version tracking
* [ ] Hash/version comparison

---

# Phase 7 - API Diff Engine

**Status: NOT STARTED**

## Goal

So sánh API mới với Integration hiện tại.

```text
Latest Provider API
          VS
Current Integration Manifest
          ↓
        Diff
```

## Detect

* [ ] Endpoint added
* [ ] Endpoint removed
* [ ] HTTP method changed
* [ ] Parameters changed
* [ ] Required field changed
* [ ] Request schema changed
* [ ] Response schema changed
* [ ] Authentication changed
* [ ] Base URL changed
* [ ] API version changed

---

# Phase 8 - Impact Analysis

**Status: NOT STARTED**

## Goal

Xác định Integration/action nào bị ảnh hưởng.

Example:

```text
Provider change

DELETE
/v1/customers

        ↓

Search current manifest

        ↓

Action:
get-customers

        ↓

IMPACTED
```

## Severity

```text
LOW
MEDIUM
HIGH
CRITICAL
```

---

# Phase 9 - Proposed Integration Update

**Status: NOT STARTED**

## Goal

Generate bản Integration mới nhưng chưa apply trực tiếp.

```text
Current Integration
        +
Detected Changes
        ↓
Proposed Integration
```

Hệ thống phải tạo diff:

```diff
- /v1/customers
+ /v2/customers
```

Không được tự động apply vào production tại bước này.

---

# Phase 10 - Notification & Admin Review

**Status: NOT STARTED**

## Goal

Thông báo cho Admin và yêu cầu review.

```text
Change detected
      ↓
Slack
      ↓
Admin Dashboard
      ↓
View Diff
      ↓
Approve / Reject
```

## Tasks

* [ ] Slack integration
* [ ] Change notification
* [ ] Admin review API
* [ ] Approve
* [ ] Reject
* [ ] Audit log

---

# Phase 11 - Integration Update

**Status: NOT STARTED**

## Goal

Chỉ apply update sau khi Admin approve.

```text
Admin Approve
      ↓
Validate
      ↓
Apply Integration Update
      ↓
Runtime Test
      ↓
Success / Rollback
```

---

# Current Development Position

```text
Phase 1   Base Communication       ← CURRENT
   ↓
Phase 2   RabbitMQ
   ↓
Phase 3   Email Processing
   ↓
Phase 4   API Change Detection
   ↓
Phase 5   Provider Resolution
   ↓
Phase 6   Documentation Verification
   ↓
Phase 7   API Diff
   ↓
Phase 8   Impact Analysis
   ↓
Phase 9   Generate Update
   ↓
Phase 10  Admin Review
   ↓
Phase 11  Apply Update
```

---

# Immediate Next Milestone

Hoàn thành:

```text
C# → FastAPI → ChangeSignal → C#
```

Sau khi end-to-end test thành công:

```text
Phase 1 DONE
     ↓
Start Phase 2
     ↓
RabbitMQ
```

Không bắt đầu LLM, crawler hoặc auto-update trước khi communication contract giữa C# và Python hoạt động ổn định.
