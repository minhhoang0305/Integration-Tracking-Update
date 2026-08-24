"""Auto-generated integration for VeriFone."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for VeriFone (api_key)."""

    BASE_URL = "https://api.veriphone.com"

    def __init__(self) -> None:
        self._api_key: Optional[str] = None

    async def initialize(
        self,
        credentials_dict: Dict[str, Any],
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._api_key = (
            credentials_dict.get("api_key")
            or credentials_dict.get("apiKey")
            or (connection_config or {}).get("api_key")
        )

    def _require_key(self) -> str:
        if not self._api_key:
            raise ValueError("api_key is required")
        return str(self._api_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._require_key()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.BASE_URL, headers=self._headers(), timeout=30.0,
        )

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "verify-credit-card":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/v1/creditcard/verify", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "process-payment":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/v1/payment/process", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-transaction-status":
                transactionId = payload.get("transactionId")
                if not transactionId:
                    raise ValueError("'transactionId' required")
                r = await client.get(f"/v1/transaction/{transactionId}/status")
                r.raise_for_status()
                return r.json()
            elif action_name == "refund-transaction":
                transactionId = payload.get("transactionId")
                if not transactionId:
                    raise ValueError("'transactionId' required")
                body = {k: v for k, v in payload.items() if k not in ['transactionId'] and v is not None}
                r = await client.post(f"/v1/transaction/{transactionId}/refund", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "void-transaction":
                transactionId = payload.get("transactionId")
                if not transactionId:
                    raise ValueError("'transactionId' required")
                r = await client.post(f"/v1/transaction/{transactionId}/void")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "veriphone"}
