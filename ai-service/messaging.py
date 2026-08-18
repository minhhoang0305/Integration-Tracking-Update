import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import aio_pika

from models import AnalyzeEmailRequest, ChangeEvidence, ChangeSignal
from rule_detector import detect_changes_with_evidence
import re

logger = logging.getLogger(__name__)

EVENTS_EXCHANGE = "integration-tracking.events"
RETRY_EXCHANGE = "integration-tracking.retry"
REQUEST_ROUTING_KEY = "email.analysis.requested"
COMPLETED_ROUTING_KEY = "email.analysis.completed"
FAILED_ROUTING_KEY = "email.analysis.failed"
DLQ_ROUTING_KEY = "email.analysis.dlq"
WORKER_QUEUE = "email.analysis.worker"
DLQ_QUEUE = "email.analysis.dlq"
RETRY_DELAYS = (10, 30, 60)


class AnalysisWorker:
    def __init__(self) -> None:
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._events_exchange: aio_pika.abc.AbstractExchange | None = None
        self._retry_exchange: aio_pika.abc.AbstractExchange | None = None

    async def start(self) -> None:
        url = os.getenv(
            "RABBITMQ_URL",
            "amqp://integration_tracking:integration_tracking@localhost:5672/",
        )
        self._connection = await aio_pika.connect_robust(url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=1)
        self._events_exchange = await self._channel.declare_exchange(
            EVENTS_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True
        )
        self._retry_exchange = await self._channel.declare_exchange(
            RETRY_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True
        )

        queue = await self._channel.declare_queue(WORKER_QUEUE, durable=True)
        await queue.bind(self._events_exchange, REQUEST_ROUTING_KEY)
        dlq = await self._channel.declare_queue(DLQ_QUEUE, durable=True)
        await dlq.bind(self._events_exchange, DLQ_ROUTING_KEY)

        for seconds in RETRY_DELAYS:
            retry_queue = await self._channel.declare_queue(
                f"email.analysis.retry.{seconds}s",
                durable=True,
                arguments={
                    "x-message-ttl": seconds * 1000,
                    "x-dead-letter-exchange": EVENTS_EXCHANGE,
                    "x-dead-letter-routing-key": REQUEST_ROUTING_KEY,
                },
            )
            await retry_queue.bind(self._retry_exchange, f"retry.{seconds}")

        await queue.consume(self._handle_message)
        logger.info("RabbitMQ analysis worker started.")

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()

    async def _handle_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process(requeue=True):
            envelope = json.loads(message.body.decode("utf-8"))
            correlation_id = envelope["correlationId"]
            retry_count = int(message.headers.get("x-retry-count", 0)) if message.headers else 0
            try:
                request = AnalyzeEmailRequest.model_validate(envelope["payload"])
                change_types, matched_terms = detect_changes_with_evidence(request.subject, request.body)
                detected = bool(change_types)
                result = ChangeSignal(
                    emailId=request.emailId,
                    isApiRelated=detected,
                    changeDetected=detected,
                    changeTypes=change_types,
                    summary="Potential API change detected." if detected else "No API change detected.",
                    breakingChange=("BREAKING_CHANGE" in change_types or "DEPRECATION" in change_types),
                    migrationRequired=("VERSION_CHANGE" in change_types or "DEPRECATION" in change_types),
                    confidence=min(0.5 + len(change_types) * 0.1, 0.95) if detected else 0.0,
                    evidence=ChangeEvidence(
                        matchedTerms=matched_terms,
                        urls=re.findall(r"https?://[^\s)]+", f"{request.subject} {request.body}"),
                    ),
                )
                await self._publish(EVENTS_EXCHANGE, COMPLETED_ROUTING_KEY, correlation_id, result.model_dump(mode="json"))
                logger.info("Completed analysis for %s", correlation_id)
            except Exception as exception:
                await self._handle_failure(envelope, correlation_id, retry_count, str(exception))

    async def _handle_failure(self, envelope: dict[str, Any], correlation_id: str, retry_count: int, error: str) -> None:
        assert self._retry_exchange is not None
        if retry_count < len(RETRY_DELAYS):
            delay = RETRY_DELAYS[retry_count]
            await self._retry_exchange.publish(
                self._message(envelope, correlation_id, headers={"x-retry-count": retry_count + 1}),
                routing_key=f"retry.{delay}",
            )
            logger.warning("Retrying analysis %s in %ss (%s/3): %s", correlation_id, delay, retry_count + 1, error)
            return

        failure = {"emailId": correlation_id, "error": error, "attempts": retry_count}
        await self._publish(EVENTS_EXCHANGE, FAILED_ROUTING_KEY, correlation_id, failure)
        assert self._events_exchange is not None
        await self._events_exchange.publish(self._message(envelope, correlation_id), routing_key=DLQ_ROUTING_KEY)
        logger.exception("Analysis %s exhausted retries: %s", correlation_id, error)

    async def _publish(self, exchange_name: str, routing_key: str, correlation_id: str, payload: dict[str, Any]) -> None:
        assert self._events_exchange is not None
        envelope = {
            "version": 1,
            "messageId": os.urandom(16).hex(),
            "correlationId": correlation_id,
            "occurredAtUtc": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        await self._events_exchange.publish(self._message(envelope, correlation_id), routing_key=routing_key)

    @staticmethod
    def _message(payload: dict[str, Any], correlation_id: str, headers: dict[str, Any] | None = None) -> aio_pika.Message:
        return aio_pika.Message(
            body=json.dumps(payload, default=str).encode("utf-8"),
            content_type="application/json",
            correlation_id=correlation_id,
            headers=headers or {},
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )


async def run_worker() -> None:
    worker = AnalysisWorker()
    await worker.start()
    try:
        await asyncio.Future()
    finally:
        await worker.close()
