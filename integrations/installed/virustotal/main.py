"""Auto-generated integration for VirusTotal."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for VirusTotal (api_key)."""

    BASE_URL = "https://www.virustotal.com/api/v3"

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
            if sync_name == "recent-files":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "recent-urls":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "analyze-file":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/files", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-file-report":
                id = payload.get("id")
                if not id:
                    raise ValueError("'id' required")
                r = await client.get(f"/files/{id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "analyze-url":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/urls", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-url-report":
                id = payload.get("id")
                if not id:
                    raise ValueError("'id' required")
                r = await client.get(f"/urls/{id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "search-files":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/files", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-domain-report":
                domain = payload.get("domain")
                if not domain:
                    raise ValueError("'domain' required")
                r = await client.get(f"/domains/{domain}")
                r.raise_for_status()
                return r.json()
            elif action_name == "analyze-domain":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/domains", json=body)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "virustotal"}
