import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    BASE_URL = "https://api.uber.com/v1.2"

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
            if action_name == "get-profile":
                resp = await client.get("/me")
                resp.raise_for_status()
                return resp.json()

            if action_name == "get-trip-history":
                params = {k: v for k, v in payload.items() if k in ("limit", "offset")}
                resp = await client.get("/history", params=params)
                resp.raise_for_status()
                return resp.json()

            if action_name == "list-products":
                params = {k: v for k, v in payload.items() if k in ("latitude", "longitude")}
                resp = await client.get("/products", params=params)
                resp.raise_for_status()
                return resp.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "uber-api"}
