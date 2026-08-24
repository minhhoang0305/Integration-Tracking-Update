"""Auto-generated integration for Zoho Invoice."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Zoho Invoice (oauth2)."""

    BASE_URL = "https://www.zohoapis.com/invoices"

    def __init__(self) -> None:
        self._token: Optional[str] = None

    async def initialize(
        self,
        credentials_dict: Dict[str, Any],
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._token = credentials_dict.get("access_token")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.BASE_URL, headers=self._headers(), timeout=30.0,
        )

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        async with self._client() as client:
            if sync_name == "invoices":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "customers":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-invoice":
                invoice_id = payload.get("invoice_id")
                if not invoice_id:
                    raise ValueError("'invoice_id' required")
                r = await client.get(f"/invoices/{invoice_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-invoices":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/invoices", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-invoice":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/invoices", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-invoice":
                invoice_id = payload.get("invoice_id")
                if not invoice_id:
                    raise ValueError("'invoice_id' required")
                body = {k: v for k, v in payload.items() if k not in ['invoice_id'] and v is not None}
                r = await client.put(f"/invoices/{invoice_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-invoice":
                invoice_id = payload.get("invoice_id")
                if not invoice_id:
                    raise ValueError("'invoice_id' required")
                r = await client.delete(f"/invoices/{invoice_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-customer":
                customer_id = payload.get("customer_id")
                if not customer_id:
                    raise ValueError("'customer_id' required")
                r = await client.get(f"/customers/{customer_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-customers":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/customers", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoho_invoice"}
