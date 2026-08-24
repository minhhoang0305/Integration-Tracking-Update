"""Auto-generated integration for You Need A Budget."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for You Need A Budget (oauth2)."""

    BASE_URL = "https://api.ynab.com/v1"

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
            if sync_name == "transactions":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "accounts":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "budgets":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-budget":
                budget_id = payload.get("budget_id")
                if not budget_id:
                    raise ValueError("'budget_id' required")
                r = await client.get(f"/budgets/{budget_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-budgets":
                r = await client.get("/budgets")
                r.raise_for_status()
                return r.json()
            elif action_name == "create-transaction":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/transactions", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-transaction":
                transaction_id = payload.get("transaction_id")
                if not transaction_id:
                    raise ValueError("'transaction_id' required")
                body = {k: v for k, v in payload.items() if k not in ['transaction_id'] and v is not None}
                r = await client.patch(f"/transactions/{transaction_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-transaction":
                transaction_id = payload.get("transaction_id")
                if not transaction_id:
                    raise ValueError("'transaction_id' required")
                r = await client.delete(f"/transactions/{transaction_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-account":
                account_id = payload.get("account_id")
                if not account_id:
                    raise ValueError("'account_id' required")
                r = await client.get(f"/accounts/{account_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-accounts":
                r = await client.get("/accounts")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-category":
                category_id = payload.get("category_id")
                if not category_id:
                    raise ValueError("'category_id' required")
                r = await client.get(f"/categories/{category_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-categories":
                r = await client.get("/categories")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "ynab"}
