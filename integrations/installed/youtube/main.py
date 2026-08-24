import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self) -> None:
        self._token: Optional[str] = None

    async def initialize(self, credentials_dict: Dict[str, Any], connection_config: Optional[Dict[str, Any]] = None) -> None:
        self._token = credentials_dict.get("access_token")

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.BASE_URL, headers=self._headers(), timeout=30.0)

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "list-videos":
                params = {k: v for k, v in payload.items() if k in ("part", "id", "chart", "maxResults")}
                resp = await client.get("/videos", params=params)
                resp.raise_for_status()
                return resp.json()

            if action_name == "search":
                params = {k: v for k, v in payload.items() if k in ("part", "q", "type", "maxResults", "pageToken")}
                resp = await client.get("/search", params=params)
                resp.raise_for_status()
                return resp.json()

            if action_name == "list-channels":
                params = {k: v for k, v in payload.items() if k in ("part", "mine", "id")}
                resp = await client.get("/channels", params=params)
                resp.raise_for_status()
                return resp.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "youtube"}
