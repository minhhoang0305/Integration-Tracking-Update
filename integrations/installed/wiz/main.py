"""Auto-generated integration for Wiz."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Wiz (api_key)."""

    BASE_URL = "https://api.wiz.io"

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
            if sync_name == "findings":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "resources":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "policies":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-finding":
                finding_id = payload.get("finding_id")
                if not finding_id:
                    raise ValueError("'finding_id' required")
                r = await client.get(f"/findings/{finding_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-findings":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/findings", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-resource":
                resource_id = payload.get("resource_id")
                if not resource_id:
                    raise ValueError("'resource_id' required")
                r = await client.get(f"/resources/{resource_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-resources":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/resources", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-policy":
                policy_id = payload.get("policy_id")
                if not policy_id:
                    raise ValueError("'policy_id' required")
                r = await client.get(f"/policies/{policy_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-policies":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/policies", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "wiz"}
