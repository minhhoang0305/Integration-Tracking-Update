"""Auto-generated integration for Wit.ai."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Wit.ai (api_key)."""

    BASE_URL = "https://api.wit.ai"

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
            if action_name == "get-app":
                app_id = payload.get("app_id")
                if not app_id:
                    raise ValueError("'app_id' required")
                r = await client.get(f"/apps/{app_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "create-intent":
                app_id = payload.get("app_id")
                if not app_id:
                    raise ValueError("'app_id' required")
                body = {k: v for k, v in payload.items() if k not in ['app_id'] and v is not None}
                r = await client.post(f"/apps/{app_id}/intents", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-intent":
                app_id = payload.get("app_id")
                intent_id = payload.get("intent_id")
                if not app_id or not intent_id:
                    raise ValueError("'app_id', 'intent_id' required")
                r = await client.get(f"/apps/{app_id}/intents/{intent_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "update-intent":
                app_id = payload.get("app_id")
                intent_id = payload.get("intent_id")
                if not app_id or not intent_id:
                    raise ValueError("'app_id', 'intent_id' required")
                body = {k: v for k, v in payload.items() if k not in ['app_id', 'intent_id'] and v is not None}
                r = await client.put(f"/apps/{app_id}/intents/{intent_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-intent":
                app_id = payload.get("app_id")
                intent_id = payload.get("intent_id")
                if not app_id or not intent_id:
                    raise ValueError("'app_id', 'intent_id' required")
                r = await client.delete(f"/apps/{app_id}/intents/{intent_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-utterances":
                app_id = payload.get("app_id")
                intent_id = payload.get("intent_id")
                if not app_id or not intent_id:
                    raise ValueError("'app_id', 'intent_id' required")
                r = await client.get(f"/apps/{app_id}/intents/{intent_id}/utterances")
                r.raise_for_status()
                return r.json()
            elif action_name == "create-utterance":
                app_id = payload.get("app_id")
                intent_id = payload.get("intent_id")
                if not app_id or not intent_id:
                    raise ValueError("'app_id', 'intent_id' required")
                body = {k: v for k, v in payload.items() if k not in ['app_id', 'intent_id'] and v is not None}
                r = await client.post(f"/apps/{app_id}/intents/{intent_id}/utterances", json=body)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "wit-ai"}
