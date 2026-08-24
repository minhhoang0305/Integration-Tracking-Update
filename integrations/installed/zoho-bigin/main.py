"""Auto-generated integration for Zoho Bigin."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Zoho Bigin (oauth2)."""

    BASE_URL = "https://www.zohoapis.com/bigin"

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
                r = await client.get("/v1/Contacts")
                r.raise_for_status()
                return r.json()
            elif sync_name == "deals":
                r = await client.get("/v1/Deals")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-contact":
                contact_id = payload.get("contact_id")
                if not contact_id:
                    raise ValueError("'contact_id' required")
                r = await client.get(f"/v1/Contacts/{contact_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-contacts":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/v1/Contacts", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-contact":
                body = {k: v for k, v in payload.items() if v is not None}
                r = await client.post("/v1/Contacts", json={"data": [body]})
                r.raise_for_status()
                return r.json()
            elif action_name == "update-contact":
                contact_id = payload.get("contact_id")
                if not contact_id:
                    raise ValueError("'contact_id' required")
                body = {k: v for k, v in payload.items() if k not in ["contact_id"] and v is not None}
                r = await client.put(f"/v1/Contacts/{contact_id}", json={"data": [body]})
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-contact":
                contact_id = payload.get("contact_id")
                if not contact_id:
                    raise ValueError("'contact_id' required")
                r = await client.delete(f"/v1/Contacts/{contact_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-deal":
                deal_id = payload.get("deal_id")
                if not deal_id:
                    raise ValueError("'deal_id' required")
                r = await client.get(f"/v1/Deals/{deal_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-deals":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/v1/Deals", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-deal":
                body = {k: v for k, v in payload.items() if v is not None}
                r = await client.post("/v1/Deals", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "update-deal":
                deal_id = payload.get("deal_id")
                if not deal_id:
                    raise ValueError("'deal_id' required")
                body = {k: v for k, v in payload.items() if k not in ["deal_id"] and v is not None}
                r = await client.put(f"/v1/Deals/{deal_id}", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-deal":
                deal_id = payload.get("deal_id")
                if not deal_id:
                    raise ValueError("'deal_id' required")
                r = await client.delete(f"/v1/Deals/{deal_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-companies":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/v1/Companies", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-company":
                company_id = payload.get("company_id")
                if not company_id:
                    raise ValueError("'company_id' required")
                r = await client.get(f"/v1/Companies/{company_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-company":
                body = {k: v for k, v in payload.items() if v is not None}
                r = await client.post("/v1/Companies", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "update-company":
                company_id = payload.get("company_id")
                if not company_id:
                    raise ValueError("'company_id' required")
                body = {k: v for k, v in payload.items() if k not in ["company_id"] and v is not None}
                r = await client.put(f"/v1/Companies/{company_id}", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-company":
                company_id = payload.get("company_id")
                if not company_id:
                    raise ValueError("'company_id' required")
                r = await client.delete(f"/v1/Companies/{company_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-pipelines":
                r = await client.get("/v1/pipelines")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-activities":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/v1/Activities", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "create-activity":
                body = {k: v for k, v in payload.items() if v is not None}
                r = await client.post("/v1/Activities", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "list-notes":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/v1/Notes", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "create-note":
                body = {k: v for k, v in payload.items() if v is not None}
                r = await client.post("/v1/Notes", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "search":
                module = payload.get("module")
                if not module:
                    raise ValueError("'module' required")
                params = {k: v for k, v in payload.items() if k not in ["module"] and v is not None}
                r = await client.get(f"/v1/{module}/search", params=params)
                r.raise_for_status()
                return r.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoho-bigin"}
