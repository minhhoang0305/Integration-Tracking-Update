"""Auto-generated integration for Zoho Mail."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Zoho Mail (oauth2)."""

    BASE_URL = "https://mail.zoho.com/api/v1"

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
            if sync_name == "messages":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "mailboxes":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-message":
                message_id = payload.get("message_id")
                if not message_id:
                    raise ValueError("'message_id' required")
                r = await client.get(f"/messages/{message_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-messages":
                mailbox_id = payload.get("mailbox_id")
                if not mailbox_id:
                    raise ValueError("'mailbox_id' required")
                params = {k: v for k, v in payload.items() if k not in ['mailbox_id'] and v is not None}
                r = await client.get(f"/mailboxes/{mailbox_id}/messages", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "send-message":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/messages", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-message":
                message_id = payload.get("message_id")
                if not message_id:
                    raise ValueError("'message_id' required")
                body = {k: v for k, v in payload.items() if k not in ['message_id'] and v is not None}
                r = await client.patch(f"/messages/{message_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-message":
                message_id = payload.get("message_id")
                if not message_id:
                    raise ValueError("'message_id' required")
                r = await client.delete(f"/messages/{message_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-mailboxes":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/mailboxes", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "search-messages":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/messages/search", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoho_mail"}
