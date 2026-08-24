"""Auto-generated integration for Zoho Desk."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Zoho Desk (oauth2)."""

    BASE_URL = "https://desk.zoho.com"

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
            if sync_name == "tickets":
                r = await client.get("/api/v1/tickets")
                r.raise_for_status()
                return r.json()
            elif sync_name == "customers":
                r = await client.get("/api/v1/customers")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-ticket":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' required")
                r = await client.get(f"/api/v1/tickets/{ticket_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-tickets":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/api/v1/tickets", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-ticket":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/api/v1/tickets", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-ticket":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' required")
                body = {k: v for k, v in payload.items() if k not in ['ticket_id'] and v is not None}
                r = await client.put(f"/api/v1/tickets/{ticket_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-ticket":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' required")
                r = await client.delete(f"/api/v1/tickets/{ticket_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-customer":
                customer_id = payload.get("customer_id")
                if not customer_id:
                    raise ValueError("'customer_id' required")
                r = await client.get(f"/api/v1/customers/{customer_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-customers":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/api/v1/customers", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-customer":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/api/v1/customers", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-customer":
                customer_id = payload.get("customer_id")
                if not customer_id:
                    raise ValueError("'customer_id' required")
                body = {k: v for k, v in payload.items() if k not in ["customer_id"] and v is not None}
                r = await client.put(f"/api/v1/customers/{customer_id}", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-customer":
                customer_id = payload.get("customer_id")
                if not customer_id:
                    raise ValueError("'customer_id' required")
                r = await client.delete(f"/api/v1/customers/{customer_id}")
                r.raise_for_status()
                return r.json() if r.content else {"deleted": True}

            elif action_name == "list-ticket-comments":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' required")
                params = {k: v for k, v in payload.items() if k not in ["ticket_id"] and v is not None}
                r = await client.get(f"/api/v1/tickets/{ticket_id}/comments", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "add-ticket-comment":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' required")
                body = {k: v for k, v in payload.items() if k not in ["ticket_id"] and v is not None}
                r = await client.post(f"/api/v1/tickets/{ticket_id}/comments", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "list-agents":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/api/v1/agents", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-agent":
                agent_id = payload.get("agent_id")
                if not agent_id:
                    raise ValueError("'agent_id' required")
                r = await client.get(f"/api/v1/agents/{agent_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-departments":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/api/v1/departments", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-department":
                dept_id = payload.get("department_id")
                if not dept_id:
                    raise ValueError("'department_id' required")
                r = await client.get(f"/api/v1/departments/{dept_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-contacts":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/api/v1/contacts", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "search-tickets":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/api/v1/tickets/search", params=params)
                r.raise_for_status()
                return r.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoho-desk"}
