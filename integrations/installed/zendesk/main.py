import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    def __init__(self):
        self.access_token: Optional[str] = None
        self.subdomain: Optional[str] = None

    async def initialize(self, credentials_dict: Dict[str, Any], connection_config: Optional[Dict[str, Any]] = None) -> None:
        self.access_token = credentials_dict.get("access_token")
        self.subdomain = (connection_config or {}).get("subdomain") or credentials_dict.get("subdomain")

    @property
    def base_url(self) -> str:
        if not self.subdomain:
            raise ValueError("'subdomain' is required in connection_config for Zendesk")
        return f"https://{self.subdomain}.zendesk.com/api/v2"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Host": f"{self.subdomain}.zendesk.com" if self.subdomain else "zendesk.com",
            "User-Agent": "nolixan/1.0",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(headers=self._headers(), timeout=30.0)

    async def execute_sync_task(self, sync_name: str = "tickets", **kwargs) -> Any:
        async with self._client() as client:
            if sync_name == "tickets":
                r = await client.get(f"{self.base_url}/tickets.json",
                                     params={"per_page": 100, "sort_by": "created_at", "sort_order": "desc"})
                r.raise_for_status()
                return r.json()
            elif sync_name == "users":
                r = await client.get(f"{self.base_url}/users.json", params={"per_page": 100})
                r.raise_for_status()
                return r.json()
            elif sync_name == "organizations":
                r = await client.get(f"{self.base_url}/organizations.json", params={"per_page": 100})
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "create-ticket":
                subject = payload.get("subject")
                if not subject:
                    raise ValueError("'subject' is required")
                ticket: Dict[str, Any] = {"subject": subject}
                if "requester_id" in payload:
                    ticket["requester_id"] = payload["requester_id"]
                if "body" in payload:
                    ticket["comment"] = {"body": payload["body"]}
                if "priority" in payload:
                    ticket["priority"] = payload["priority"]
                if "status" in payload:
                    ticket["status"] = payload["status"]
                if "tags" in payload:
                    ticket["tags"] = payload["tags"]
                r = await client.post(f"{self.base_url}/tickets.json", json={"ticket": ticket})
                r.raise_for_status()
                return r.json()

            elif action_name == "update-ticket":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' is required")
                ticket = {k: v for k, v in payload.items() if k != "ticket_id"}
                r = await client.put(f"{self.base_url}/tickets/{ticket_id}.json", json={"ticket": ticket})
                r.raise_for_status()
                return r.json()

            elif action_name == "get-ticket":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' is required")
                r = await client.get(f"{self.base_url}/tickets/{ticket_id}.json")
                r.raise_for_status()
                return r.json()

            elif action_name == "add-comment":
                ticket_id = payload.get("ticket_id")
                body = payload.get("body")
                if not ticket_id or not body:
                    raise ValueError("'ticket_id' and 'body' are required")
                is_public = payload.get("public", True)
                r = await client.put(
                    f"{self.base_url}/tickets/{ticket_id}.json",
                    json={"ticket": {"comment": {"body": body, "public": is_public}}}
                )
                r.raise_for_status()
                return r.json()

            elif action_name == "close-ticket":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' is required")
                r = await client.put(f"{self.base_url}/tickets/{ticket_id}.json",
                                     json={"ticket": {"status": "closed"}})
                r.raise_for_status()
                return r.json()

            elif action_name == "search-tickets":
                query = payload.get("query")
                if not query:
                    raise ValueError("'query' is required")
                r = await client.get(f"{self.base_url}/search.json",
                                     params={"query": f"type:ticket {query}"})
                r.raise_for_status()
                return r.json()

            elif action_name == "create-user":
                name = payload.get("name")
                email = payload.get("email")
                if not name or not email:
                    raise ValueError("'name' and 'email' are required")
                r = await client.post(f"{self.base_url}/users.json",
                                      json={"user": {"name": name, "email": email}})
                r.raise_for_status()
                return r.json()

            elif action_name == "list-tickets":
                params = {
                    "per_page": payload.get("per_page", 100),
                    "sort_by": payload.get("sort_by", "created_at"),
                    "sort_order": payload.get("sort_order", "desc"),
                }
                r = await client.get(f"{self.base_url}/tickets.json", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-ticket":
                ticket_id = payload.get("ticket_id")
                if not ticket_id:
                    raise ValueError("'ticket_id' is required")
                r = await client.delete(f"{self.base_url}/tickets/{ticket_id}.json")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "get-user":
                user_id = payload.get("user_id")
                if not user_id:
                    raise ValueError("'user_id' is required")
                r = await client.get(f"{self.base_url}/users/{user_id}.json")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-users":
                params = {"per_page": payload.get("per_page", 100)}
                if payload.get("role"):
                    params["role"] = payload["role"]
                r = await client.get(f"{self.base_url}/users.json", params=params)
                r.raise_for_status()
                return r.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zendesk"}
