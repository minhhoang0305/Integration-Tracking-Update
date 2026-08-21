# Docker local pipeline

This runbook starts the core pipeline without Gmail OAuth, Pub/Sub, an LLM key, or Vault:

```text
POST /api/emails/analyze -> RabbitMQ -> Python AI worker -> PostgreSQL
```

## Start

Copy the local-only defaults, then build and start all four services:

```sh
cp .env.example .env
docker compose up --build -d
docker compose ps
```

On PowerShell, use `Copy-Item .env.example .env` instead of `cp`.

The passwords in `.env.example` are intentionally local-only defaults, matching the existing Docker setup. Do not reuse them outside local development.

The backend is at `http://localhost:5000`, Swagger is at `http://localhost:5000/swagger`, and RabbitMQ management is at `http://localhost:15672`.

Check the backend and worker:

```sh
curl http://localhost:5000/health
docker compose logs ai-worker
```

The worker log must include `RabbitMQ analysis worker started.`

## Test the pipeline

```sh
curl --request POST http://localhost:5000/api/emails/analyze \
  --header 'Content-Type: application/json' \
  --data '{"emailId":"docker-e2e-001","sender":"updates@example.com","subject":"API v1 deprecation notice","body":"The API v1 endpoint is deprecated. Migrate to API v2.","receivedAt":"2026-08-21T00:00:00Z"}'
```

Poll for a completed result:

```sh
curl http://localhost:5000/api/email-analyses/docker-e2e-001
```

Submit the same `emailId` again to verify idempotency. The API returns the existing analysis instead of creating a second one.

## Stop

```sh
docker compose down
```

This keeps the PostgreSQL, RabbitMQ, and proposal volumes. Do not use `docker compose down -v` unless you intentionally want to delete local data.
