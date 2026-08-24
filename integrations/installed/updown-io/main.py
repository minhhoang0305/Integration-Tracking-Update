"""Auto-generated integration for Updown.io."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Updown.io (api_key)."""

    BASE_URL = "https://api.updown.io"

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
        async with self._client() as client:
            if sync_name == "checks":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-check":
                checkId = payload.get("checkId")
                if not checkId:
                    raise ValueError("'checkId' required")
                r = await client.get(f"/checks/{checkId}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-checks":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/checks", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-check":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/checks", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-check":
                checkId = payload.get("checkId")
                if not checkId:
                    raise ValueError("'checkId' required")
                body = {k: v for k, v in payload.items() if k not in ['checkId'] and v is not None}
                r = await client.patch(f"/checks/{checkId}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-check":
                checkId = payload.get("checkId")
                if not checkId:
                    raise ValueError("'checkId' required")
                r = await client.delete(f"/checks/{checkId}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-check-history":
                checkId = payload.get("checkId")
                if not checkId:
                    raise ValueError("'checkId' required")
                params = {k: v for k, v in payload.items() if k not in ['checkId'] and v is not None}
                r = await client.get(f"/checks/{checkId}/history", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "updown-io"}
