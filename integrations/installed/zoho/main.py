"""Auto-generated integration for Zoho CRM."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Zoho CRM (oauth2)."""

    BASE_URL = "https://www.zohoapis.com"

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
            if sync_name == "contacts":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "deals":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-contact":
                contact_id = payload.get("contact_id")
                if not contact_id:
                    raise ValueError("'contact_id' required")
                r = await client.get(f"/crm/v2/contacts/{contact_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-contacts":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/crm/v2/contacts", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-contact":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/crm/v2/contacts", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-contact":
                contact_id = payload.get("contact_id")
                if not contact_id:
                    raise ValueError("'contact_id' required")
                body = {k: v for k, v in payload.items() if k not in ['contact_id'] and v is not None}
                r = await client.put(f"/crm/v2/contacts/{contact_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-contact":
                contact_id = payload.get("contact_id")
                if not contact_id:
                    raise ValueError("'contact_id' required")
                r = await client.delete(f"/crm/v2/contacts/{contact_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "search-contacts":
                query = payload.get("query")
                if not query:
                    raise ValueError("'query' required")
                r = await client.get(f"/crm/v2/contacts/search?q={query}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-deal":
                deal_id = payload.get("deal_id")
                if not deal_id:
                    raise ValueError("'deal_id' required")
                r = await client.get(f"/crm/v2/deals/{deal_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-deals":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/crm/v2/deals", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoho"}
