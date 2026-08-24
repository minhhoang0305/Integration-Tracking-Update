"""Auto-generated integration for U301."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for U301 (api_key)."""

    BASE_URL = "https://api.u301.com"

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
            if sync_name == "domain_rankings":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "backlink_counts":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-domain-info":
                domain = payload.get("domain")
                if not domain:
                    raise ValueError("'domain' required")
                r = await client.get(f"/domains/{domain}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-keyword-overview":
                keyword = payload.get("keyword")
                if not keyword:
                    raise ValueError("'keyword' required")
                r = await client.get(f"/keywords/{keyword}/overview")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-keyword-suggestions":
                keyword = payload.get("keyword")
                if not keyword:
                    raise ValueError("'keyword' required")
                r = await client.get(f"/keywords/{keyword}/suggestions")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-backlink-count":
                domain = payload.get("domain")
                if not domain:
                    raise ValueError("'domain' required")
                r = await client.get(f"/domains/{domain}/backlinks/count")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-competitors":
                domain = payload.get("domain")
                if not domain:
                    raise ValueError("'domain' required")
                r = await client.get(f"/domains/{domain}/competitors")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-ranking-history":
                keyword = payload.get("keyword")
                domain = payload.get("domain")
                if not keyword or not domain:
                    raise ValueError("'keyword', 'domain' required")
                r = await client.get(f"/keywords/{keyword}/domains/{domain}/history")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-site-audit":
                domain = payload.get("domain")
                if not domain:
                    raise ValueError("'domain' required")
                r = await client.get(f"/domains/{domain}/audit")
                r.raise_for_status()
                return r.json()
            elif action_name == "search-keywords":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/keywords/search", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "u301"}
