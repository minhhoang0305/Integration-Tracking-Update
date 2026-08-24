"""Auto-generated integration for Zoho Inventory."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Zoho Inventory (oauth2)."""

    BASE_URL = "https://inventory.zoho.com/api/v1"

    def __init__(self) -> None:
        self._token: Optional[str] = None

    async def initialize(
        self,
        credentials_dict: Dict[str, Any],
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._token = credentials_dict.get("access_token")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.BASE_URL, headers=self._headers(), timeout=30.0,
        )

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        async with self._client() as client:
            if sync_name == "items":
                r = await client.get("/items")
                r.raise_for_status()
                return r.json()
            elif sync_name == "orders":
                r = await client.get("/salesorders")
                r.raise_for_status()
                return r.json()
            elif sync_name == "customers":
                r = await client.get("/contacts", params={"contact_type": "customer"})
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-item":
                item_id = payload.get("item_id")
                if not item_id:
                    raise ValueError("'item_id' required")
                r = await client.get(f"/items/{item_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-items":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/items", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-item":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/items", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-item":
                item_id = payload.get("item_id")
                if not item_id:
                    raise ValueError("'item_id' required")
                body = {k: v for k, v in payload.items() if k not in ['item_id'] and v is not None}
                r = await client.put(f"/items/{item_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "delete-item":
                item_id = payload.get("item_id")
                if not item_id:
                    raise ValueError("'item_id' required")
                r = await client.delete(f"/items/{item_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-order":
                order_id = payload.get("order_id")
                if not order_id:
                    raise ValueError("'order_id' required")
                r = await client.get(f"/salesorders/{order_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-orders":
                params = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.get("/salesorders", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-order":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/salesorders", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "update-order":
                order_id = payload.get("order_id")
                if not order_id:
                    raise ValueError("'order_id' required")
                body = {k: v for k, v in payload.items() if k not in ['order_id'] and v is not None}
                r = await client.put(f"/salesorders/{order_id}", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "get-customer":
                customer_id = payload.get("customer_id")
                if not customer_id:
                    raise ValueError("'customer_id' required")
                r = await client.get(f"/contacts/{customer_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-customers":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/contacts", params={"contact_type": "customer", **params})
                r.raise_for_status()
                return r.json()

            elif action_name == "create-customer":
                body = {k: v for k, v in payload.items() if v is not None}
                r = await client.post("/contacts", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-customer":
                customer_id = payload.get("customer_id")
                if not customer_id:
                    raise ValueError("'customer_id' required")
                body = {k: v for k, v in payload.items() if k not in ["customer_id"] and v is not None}
                r = await client.put(f"/contacts/{customer_id}", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-customer":
                customer_id = payload.get("customer_id")
                if not customer_id:
                    raise ValueError("'customer_id' required")
                r = await client.delete(f"/contacts/{customer_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-order":
                order_id = payload.get("order_id")
                if not order_id:
                    raise ValueError("'order_id' required")
                r = await client.delete(f"/salesorders/{order_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-warehouses":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/warehouses", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-warehouse":
                warehouse_id = payload.get("warehouse_id")
                if not warehouse_id:
                    raise ValueError("'warehouse_id' required")
                r = await client.get(f"/warehouses/{warehouse_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "list-purchase-orders":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/purchaseorders", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-purchase-order":
                po_id = payload.get("purchaseorder_id")
                if not po_id:
                    raise ValueError("'purchaseorder_id' required")
                r = await client.get(f"/purchaseorders/{po_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-purchase-order":
                body = {k: v for k, v in payload.items() if v is not None}
                r = await client.post("/purchaseorders", json=body)
                r.raise_for_status()
                return r.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoho-inventory"}
