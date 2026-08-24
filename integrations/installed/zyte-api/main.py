"""Auto-generated integration for Zyte API."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Zyte API (api_key)."""

    BASE_URL = "https://api.zyte.com/crawl"

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
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "start-crawl":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/v1/crawl", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-crawl-status":
                crawl_id = payload.get("crawl_id")
                if not crawl_id:
                    raise ValueError("'crawl_id' required")
                r = await client.get(f"/v1/crawl/{crawl_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-crawl-results":
                crawl_id = payload.get("crawl_id")
                if not crawl_id:
                    raise ValueError("'crawl_id' required")
                r = await client.get(f"/v1/crawl/{crawl_id}/results")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-spiders":
                r = await client.get("/v1/spiders")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-spider-details":
                spider_name = payload.get("spider_name")
                if not spider_name:
                    raise ValueError("'spider_name' required")
                r = await client.get(f"/v1/spiders/{spider_name}")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zyte-api"}
