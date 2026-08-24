"""Auto-generated integration for Woodpecker."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Woodpecker (api_key)."""

    BASE_URL = "https://api.woodpecker.co/v1"

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
            if sync_name == "sync_analyses":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "sync_repos":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-analysis":
                analysis_id = payload.get("analysis_id")
                if not analysis_id:
                    raise ValueError("'analysis_id' required")
                r = await client.get(f"/analyses/{analysis_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-analyses":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/analyses", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-analysis":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/analyses", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-repo":
                repo_id = payload.get("repo_id")
                if not repo_id:
                    raise ValueError("'repo_id' required")
                r = await client.get(f"/repos/{repo_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-repos":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/repos", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-repo":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/repos", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-repo":
                repo_id = payload.get("repo_id")
                if not repo_id:
                    raise ValueError("'repo_id' required")
                r = await client.delete(f"/repos/{repo_id}")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "woodpecker-co"}
