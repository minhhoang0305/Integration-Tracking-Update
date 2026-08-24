"""Auto-generated integration for Yandex Disk."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Yandex Disk (api_key)."""

    BASE_URL = "https://api.yandex.net"

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
            if sync_name == "disk_files":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-folder-info":
                folder_id = payload.get("folder_id")
                if not folder_id:
                    raise ValueError("'folder_id' required")
                r = await client.get(f"/disk/v1/resources/folders/{folder_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "upload-file":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/disk/v1/resources/upload", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "download-file":
                file_path = payload.get("file_path")
                if not file_path:
                    raise ValueError("'file_path' required")
                r = await client.get(f"/disk/v1/resources/download?path={file_path}")
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-file":
                file_path = payload.get("file_path")
                if not file_path:
                    raise ValueError("'file_path' required")
                r = await client.delete(f"/disk/v1/resources/files/{file_path}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-folder-contents":
                folder_id = payload.get("folder_id")
                if not folder_id:
                    raise ValueError("'folder_id' required")
                r = await client.get(f"/disk/v1/resources/folders/{folder_id}/contents")
                r.raise_for_status()
                return r.json()
            elif action_name == "create-folder":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/disk/v1/resources/folders", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-disk-space":
                r = await client.get("/disk/v1/resources/storage")
                r.raise_for_status()
                return r.json()
            elif action_name == "copy-file":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/disk/v1/resources/copy", json=body)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "yandex"}
