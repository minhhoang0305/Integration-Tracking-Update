import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    BASE_URL = "https://nla.zapier.com/api/v1"

    def __init__(self) -> None:
        self._api_key: Optional[str] = None

    async def initialize(self, credentials_dict: Dict[str, Any], connection_config: Optional[Dict[str, Any]] = None) -> None:
        self._api_key = credentials_dict.get("api_key")

    def _headers(self) -> Dict[str, str]:
        return {"x-api-key": self._api_key, "Content-Type": "application/json"}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.BASE_URL, headers=self._headers(), timeout=30.0)

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "list-actions":
                resp = await client.get("/exposed/")
                resp.raise_for_status()
                return resp.json()

            if action_name == "execute-action":
                action_id = payload["action_id"]
                body = {k: v for k, v in payload.items() if k in ("instructions", "params", "preview_only")}
                resp = await client.post(f"/exposed/{action_id}/execute/", json=body)
                resp.raise_for_status()
                return resp.json()

            if action_name == "check-action-result":
                execution_log_id = payload["execution_log_id"]
                resp = await client.get(f"/check/{execution_log_id}/")
                resp.raise_for_status()
                return resp.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zapier"}
