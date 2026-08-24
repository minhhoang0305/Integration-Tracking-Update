"""Auto-generated integration for Webex."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Webex (oauth2)."""

    BASE_URL = "https://api.webex.com"

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
            if sync_name == "rooms":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "users":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-room":
                roomId = payload.get("roomId")
                if not roomId:
                    raise ValueError("'roomId' required")
                r = await client.get(f"/v1/rooms/{roomId}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-rooms":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/v1/rooms", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-room":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/v1/rooms", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-room":
                roomId = payload.get("roomId")
                if not roomId:
                    raise ValueError("'roomId' required")
                r = await client.delete(f"/v1/rooms/{roomId}")
                r.raise_for_status()
                return r.json()
            elif action_name == "send-message":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/v1/messages", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-message":
                messageId = payload.get("messageId")
                if not messageId:
                    raise ValueError("'messageId' required")
                r = await client.get(f"/v1/messages/{messageId}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-messages":
                roomId = payload.get("roomId")
                if not roomId:
                    raise ValueError("'roomId' required")
                params = {k: v for k, v in payload.items() if k not in ['roomId'] and v is not None}
                r = await client.get(f"/v1/rooms/{roomId}/messages", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-user":
                personId = payload.get("personId")
                if not personId:
                    raise ValueError("'personId' required")
                r = await client.get(f"/v1/people/{personId}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-users":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/v1/people", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "webex"}
