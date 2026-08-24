"""Auto-generated integration for whautomate."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for whautomate (api_key)."""

    BASE_URL = "https://api.whautomate.com"

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
            if sync_name == "workflows":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-workflow":
                workflow_id = payload.get("workflow_id")
                if not workflow_id:
                    raise ValueError("'workflow_id' required")
                r = await client.get(f"/workflows/{workflow_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-workflows":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/workflows", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-workflow":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/workflows", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-workflow":
                workflow_id = payload.get("workflow_id")
                if not workflow_id:
                    raise ValueError("'workflow_id' required")
                body = {k: v for k, v in payload.items() if k not in ['workflow_id'] and v is not None}
                r = await client.put(f"/workflows/{workflow_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-workflow":
                workflow_id = payload.get("workflow_id")
                if not workflow_id:
                    raise ValueError("'workflow_id' required")
                r = await client.delete(f"/workflows/{workflow_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "run-workflow":
                workflow_id = payload.get("workflow_id")
                if not workflow_id:
                    raise ValueError("'workflow_id' required")
                body = {k: v for k, v in payload.items() if k not in ['workflow_id'] and v is not None}
                r = await client.post(f"/workflows/{workflow_id}/run", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-workflow-run":
                workflow_id = payload.get("workflow_id")
                run_id = payload.get("run_id")
                if not workflow_id or not run_id:
                    raise ValueError("'workflow_id', 'run_id' required")
                r = await client.get(f"/workflows/{workflow_id}/runs/{run_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-workflow-runs":
                workflow_id = payload.get("workflow_id")
                if not workflow_id:
                    raise ValueError("'workflow_id' required")
                params = {k: v for k, v in payload.items() if k not in ['workflow_id'] and v is not None}
                r = await client.get(f"/workflows/{workflow_id}/runs", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "whautomate"}
