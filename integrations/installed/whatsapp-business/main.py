import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self) -> None:
        self._api_key: Optional[str] = None
        self._phone_number_id: Optional[str] = None

    async def initialize(self, credentials_dict: Dict[str, Any], connection_config: Optional[Dict[str, Any]] = None) -> None:
        self._api_key = credentials_dict.get("api_key")
        if connection_config:
            self._phone_number_id = connection_config.get("phone_number_id")

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.BASE_URL, headers=self._headers(), timeout=30.0)

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "send-text-message":
                phone_number_id = payload["phone_number_id"]
                body = {"messaging_product": "whatsapp", "to": payload["to"], "type": "text", "text": payload["text"]}
                resp = await client.post(f"/{phone_number_id}/messages", json=body)
                resp.raise_for_status()
                return resp.json()

            if action_name == "send-template-message":
                phone_number_id = payload["phone_number_id"]
                body = {"messaging_product": "whatsapp", "to": payload["to"], "type": "template", "template": payload["template"]}
                resp = await client.post(f"/{phone_number_id}/messages", json=body)
                resp.raise_for_status()
                return resp.json()

            if action_name == "get-business-profile":
                phone_number_id = payload["phone_number_id"]
                params = {}
                if "fields" in payload:
                    params["fields"] = payload["fields"]
                resp = await client.get(f"/{phone_number_id}/whatsapp_business_profile", params=params)
                resp.raise_for_status()
                return resp.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "whatsapp-business"}
