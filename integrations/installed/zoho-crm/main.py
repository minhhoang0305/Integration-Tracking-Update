import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    BASE_URL = "https://www.zohoapis.com/crm/v3"

    def __init__(self) -> None:
        self._token: Optional[str] = None

    async def initialize(self, credentials_dict: Dict[str, Any], connection_config: Optional[Dict[str, Any]] = None) -> None:
        self._token = credentials_dict.get("access_token")

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Zoho-oauthtoken {self._token}", "Content-Type": "application/json"}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.BASE_URL, headers=self._headers(), timeout=30.0)

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "list-contacts":
                r = await client.get("/Contacts", params={k: v for k, v in payload.items() if v is not None})
                r.raise_for_status()
                return r.json()

            elif action_name == "get-contact":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                r = await client.get(f"/Contacts/{record_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-contact":
                if not payload.get("Last_Name"):
                    raise ValueError("'Last_Name' is required")
                r = await client.post("/Contacts", json={"data": [{k: v for k, v in payload.items() if v is not None}]})
                r.raise_for_status()
                return r.json()

            elif action_name == "update-contact":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                body = {k: v for k, v in payload.items() if k != "id" and v is not None}
                r = await client.put(f"/Contacts/{record_id}", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "list-leads":
                r = await client.get("/Leads", params={k: v for k, v in payload.items() if v is not None})
                r.raise_for_status()
                return r.json()

            elif action_name == "get-lead":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                r = await client.get(f"/Leads/{record_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-lead":
                if not payload.get("Last_Name") or not payload.get("Company"):
                    raise ValueError("'Last_Name' and 'Company' are required")
                r = await client.post("/Leads", json={"data": [{k: v for k, v in payload.items() if v is not None}]})
                r.raise_for_status()
                return r.json()

            elif action_name == "update-lead":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                body = {k: v for k, v in payload.items() if k != "id" and v is not None}
                r = await client.put(f"/Leads/{record_id}", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "list-deals":
                r = await client.get("/Deals", params={k: v for k, v in payload.items() if v is not None})
                r.raise_for_status()
                return r.json()

            elif action_name == "create-deal":
                if not payload.get("Deal_Name") or not payload.get("Stage"):
                    raise ValueError("'Deal_Name' and 'Stage' are required")
                r = await client.post("/Deals", json={"data": [{k: v for k, v in payload.items() if v is not None}]})
                r.raise_for_status()
                return r.json()

            elif action_name == "update-deal":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                body = {k: v for k, v in payload.items() if k != "id" and v is not None}
                r = await client.put(f"/Deals/{record_id}", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-record":
                module = payload.get("module")
                record_id = payload.get("id")
                if not module or not record_id:
                    raise ValueError("'module' and 'id' are required")
                r = await client.delete(f"/{module}/{record_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "search":
                module = payload.get("module")
                if not module:
                    raise ValueError("'module' is required")
                params = {k: v for k, v in payload.items() if k != "module" and v is not None}
                r = await client.get(f"/{module}/search", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-deal":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                r = await client.get(f"/Deals/{record_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-accounts":
                r = await client.get("/Accounts", params={k: v for k, v in payload.items() if v is not None})
                r.raise_for_status()
                return r.json()

            elif action_name == "get-account":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                r = await client.get(f"/Accounts/{record_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-account":
                if not payload.get("Account_Name"):
                    raise ValueError("'Account_Name' is required")
                r = await client.post("/Accounts", json={"data": [{k: v for k, v in payload.items() if v is not None}]})
                r.raise_for_status()
                return r.json()

            elif action_name == "update-account":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                body = {k: v for k, v in payload.items() if k != "id" and v is not None}
                r = await client.put(f"/Accounts/{record_id}", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "list-notes":
                r = await client.get("/Notes", params={k: v for k, v in payload.items() if v is not None})
                r.raise_for_status()
                return r.json()

            elif action_name == "create-note":
                if not payload.get("Note_Title") or not payload.get("Parent_Id"):
                    raise ValueError("'Note_Title' and 'Parent_Id' are required")
                r = await client.post("/Notes", json={"data": [{k: v for k, v in payload.items() if v is not None}]})
                r.raise_for_status()
                return r.json()

            elif action_name == "list-tasks":
                r = await client.get("/Tasks", params={k: v for k, v in payload.items() if v is not None})
                r.raise_for_status()
                return r.json()

            elif action_name == "create-task":
                if not payload.get("Subject"):
                    raise ValueError("'Subject' is required")
                r = await client.post("/Tasks", json={"data": [{k: v for k, v in payload.items() if v is not None}]})
                r.raise_for_status()
                return r.json()

            elif action_name == "list-users":
                r = await client.get("/users", params={k: v for k, v in payload.items() if v is not None})
                r.raise_for_status()
                return r.json()

            elif action_name == "list-modules":
                r = await client.get("/settings/modules")
                r.raise_for_status()
                return r.json()

            elif action_name == "convert-lead":
                record_id = payload.get("id")
                if not record_id:
                    raise ValueError("'id' is required")
                body = {k: v for k, v in payload.items() if k != "id" and v is not None}
                r = await client.post(f"/Leads/{record_id}/actions/convert", json={"data": [body]})
                r.raise_for_status()
                return r.json()

            elif action_name == "get-related-records":
                module = payload.get("module")
                record_id = payload.get("id")
                related_module = payload.get("related_module")
                if not module or not record_id or not related_module:
                    raise ValueError("'module', 'id', and 'related_module' are required")
                params = {k: v for k, v in payload.items() if k not in ["module", "id", "related_module"] and v is not None}
                r = await client.get(f"/{module}/{record_id}/{related_module}", params=params)
                r.raise_for_status()
                return r.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoho-crm"}
