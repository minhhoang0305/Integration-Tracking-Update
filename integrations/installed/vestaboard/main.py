"""Auto-generated integration for Vestaboard."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Vestaboard (api_key)."""

    BASE_URL = "https://api.vestaboard.com"

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
            if sync_name == "boards":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "columns":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-board":
                board_id = payload.get("board_id")
                if not board_id:
                    raise ValueError("'board_id' required")
                r = await client.get(f"/boards/{board_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-boards":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/boards", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-board":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/boards", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-board":
                board_id = payload.get("board_id")
                if not board_id:
                    raise ValueError("'board_id' required")
                body = {k: v for k, v in payload.items() if k not in ['board_id'] and v is not None}
                r = await client.put(f"/boards/{board_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-board":
                board_id = payload.get("board_id")
                if not board_id:
                    raise ValueError("'board_id' required")
                r = await client.delete(f"/boards/{board_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-column":
                column_id = payload.get("column_id")
                if not column_id:
                    raise ValueError("'column_id' required")
                r = await client.get(f"/columns/{column_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-columns":
                board_id = payload.get("board_id")
                if not board_id:
                    raise ValueError("'board_id' required")
                r = await client.get(f"/boards/{board_id}/columns")
                r.raise_for_status()
                return r.json()
            elif action_name == "create-column":
                board_id = payload.get("board_id")
                if not board_id:
                    raise ValueError("'board_id' required")
                body = {k: v for k, v in payload.items() if k not in ['board_id'] and v is not None}
                r = await client.post(f"/boards/{board_id}/columns", json=body)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "vestaboard"}
