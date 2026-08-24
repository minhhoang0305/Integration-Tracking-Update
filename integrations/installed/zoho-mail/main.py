import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    BASE_URL = "https://mail.zoho.com/api"

    def __init__(self) -> None:
        self._token: Optional[str] = None

    async def initialize(self, credentials_dict: Dict[str, Any], connection_config: Optional[Dict[str, Any]] = None) -> None:
        self._token = credentials_dict.get("access_token")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Zoho-oauthtoken {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.BASE_URL, headers=self._headers(), timeout=30.0)

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        async with self._client() as client:
            if sync_name == "emails":
                account_id = kwargs.get("account_id")
                if not account_id:
                    raise ValueError("'account_id' required for emails sync")
                r = await client.get(f"/accounts/{account_id}/messages/view")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "list-accounts":
                r = await client.get("/accounts")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-messages":
                account_id = payload.get("account_id")
                if not account_id:
                    raise ValueError("'account_id' required")
                params = {k: v for k, v in payload.items() if k not in ["account_id"] and v is not None}
                r = await client.get(f"/accounts/{account_id}/messages/view", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-message":
                account_id = payload.get("account_id")
                message_id = payload.get("message_id")
                if not account_id or not message_id:
                    raise ValueError("'account_id' and 'message_id' required")
                r = await client.get(f"/accounts/{account_id}/messages/{message_id}/content")
                r.raise_for_status()
                return r.json()

            elif action_name == "send-email":
                account_id = payload.get("account_id")
                if not account_id:
                    raise ValueError("'account_id' required")
                body = {k: v for k, v in payload.items() if k not in ["account_id"] and v is not None}
                r = await client.post(f"/accounts/{account_id}/messages", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-message":
                account_id = payload.get("account_id")
                message_id = payload.get("message_id")
                if not account_id or not message_id:
                    raise ValueError("'account_id' and 'message_id' required")
                r = await client.delete(f"/accounts/{account_id}/messages/{message_id}")
                r.raise_for_status()
                return r.json() if r.content else {"deleted": True}

            elif action_name == "move-message":
                account_id = payload.get("account_id")
                message_id = payload.get("message_id")
                folder_id = payload.get("folder_id")
                if not account_id or not message_id or not folder_id:
                    raise ValueError("'account_id', 'message_id', and 'folder_id' required")
                r = await client.post(
                    f"/accounts/{account_id}/messages/{message_id}/move",
                    json={"folderId": folder_id},
                )
                r.raise_for_status()
                return r.json()

            elif action_name == "mark-as-read":
                account_id = payload.get("account_id")
                message_id = payload.get("message_id")
                if not account_id or not message_id:
                    raise ValueError("'account_id' and 'message_id' required")
                r = await client.put(
                    f"/accounts/{account_id}/updatemessage",
                    json={"mode": "markAsRead", "messageId": [message_id]},
                )
                r.raise_for_status()
                return r.json()

            elif action_name == "mark-as-unread":
                account_id = payload.get("account_id")
                message_id = payload.get("message_id")
                if not account_id or not message_id:
                    raise ValueError("'account_id' and 'message_id' required")
                r = await client.put(
                    f"/accounts/{account_id}/updatemessage",
                    json={"mode": "markAsUnread", "messageId": [message_id]},
                )
                r.raise_for_status()
                return r.json()

            elif action_name == "list-folders":
                account_id = payload.get("account_id")
                if not account_id:
                    raise ValueError("'account_id' required")
                r = await client.get(f"/accounts/{account_id}/folders")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-folder":
                account_id = payload.get("account_id")
                folder_name = payload.get("folder_name")
                if not account_id or not folder_name:
                    raise ValueError("'account_id' and 'folder_name' required")
                body: Dict[str, Any] = {"folderName": folder_name}
                if payload.get("parent_folder_id"):
                    body["parentFolderId"] = payload["parent_folder_id"]
                r = await client.post(f"/accounts/{account_id}/folders", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-folder":
                account_id = payload.get("account_id")
                folder_id = payload.get("folder_id")
                if not account_id or not folder_id:
                    raise ValueError("'account_id' and 'folder_id' required")
                r = await client.delete(f"/accounts/{account_id}/folders/{folder_id}")
                r.raise_for_status()
                return r.json() if r.content else {"deleted": True}

            elif action_name == "list-attachments":
                account_id = payload.get("account_id")
                message_id = payload.get("message_id")
                if not account_id or not message_id:
                    raise ValueError("'account_id' and 'message_id' required")
                r = await client.get(f"/accounts/{account_id}/messages/{message_id}/attachmentinfo")
                r.raise_for_status()
                return r.json()

            elif action_name == "search-messages":
                account_id = payload.get("account_id")
                if not account_id:
                    raise ValueError("'account_id' required")
                params = {k: v for k, v in payload.items() if k not in ["account_id"] and v is not None}
                r = await client.get(f"/accounts/{account_id}/messages/search", params=params)
                r.raise_for_status()
                return r.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoho-mail"}
