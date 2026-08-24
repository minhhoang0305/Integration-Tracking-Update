"""Auto-generated integration for Waiverfile."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Waiverfile (api_key)."""

    BASE_URL = "https://api.waiverfile.com"

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
            if sync_name == "waivers":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-waiver":
                waiver_id = payload.get("waiver_id")
                if not waiver_id:
                    raise ValueError("'waiver_id' required")
                r = await client.get(f"/waivers/{waiver_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "create-waiver":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/waivers", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-waiver":
                waiver_id = payload.get("waiver_id")
                if not waiver_id:
                    raise ValueError("'waiver_id' required")
                body = {k: v for k, v in payload.items() if k not in ['waiver_id'] and v is not None}
                r = await client.put(f"/waivers/{waiver_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-waiver":
                waiver_id = payload.get("waiver_id")
                if not waiver_id:
                    raise ValueError("'waiver_id' required")
                r = await client.delete(f"/waivers/{waiver_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-waivers":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/waivers", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-waiver-version":
                waiver_id = payload.get("waiver_id")
                version_id = payload.get("version_id")
                if not waiver_id or not version_id:
                    raise ValueError("'waiver_id', 'version_id' required")
                r = await client.get(f"/waivers/{waiver_id}/versions/{version_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-waiver-versions":
                waiver_id = payload.get("waiver_id")
                if not waiver_id:
                    raise ValueError("'waiver_id' required")
                params = {k: v for k, v in payload.items() if k not in ['waiver_id'] and v is not None}
                r = await client.get(f"/waivers/{waiver_id}/versions", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "waiverfile"}
