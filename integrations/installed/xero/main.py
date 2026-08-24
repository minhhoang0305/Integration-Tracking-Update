import httpx
from typing import Any, Dict, List, Optional

from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    def __init__(self) -> None:
        self._access_token: Optional[str] = None
        self._tenant_id: Optional[str] = None
        self._base_url = "https://api.xero.com/api.xro/2.0"

    async def initialize(
        self,
        credentials_dict: Dict[str, Any],
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        tokens = credentials_dict.get("tokens")
        if not isinstance(tokens, dict):
            tokens = {}

        self._access_token = (
            credentials_dict.get("access_token")
            or credentials_dict.get("accessToken")
            or tokens.get("access_token")
            or tokens.get("accessToken")
        )

        if not self._access_token:
            available = ", ".join(sorted(credentials_dict.keys())) or "none"
            raise ValueError(
                "Xero access_token is required. "
                f"Available credential keys: {available}"
            )

        cfg = connection_config or {}
        self._tenant_id = (
            cfg.get("tenant_id")
            or cfg.get("tenantId")
            or credentials_dict.get("tenant_id")
            or credentials_dict.get("tenantId")
        )
        if not self._tenant_id:
            self._tenant_id = await self._fetch_first_tenant_id()

    async def _fetch_first_tenant_id(self) -> str:
        async with httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
            },
            timeout=30.0,
        ) as client:
            response = await client.get("https://api.xero.com/connections")
            response.raise_for_status()
            connections = response.json()
            if not connections:
                raise ValueError(
                    "No Xero organizations connected. Complete the OAuth flow first."
                )
            return connections[0]["tenantId"]

    def _client(self) -> httpx.AsyncClient:
        if not self._access_token:
            raise ValueError("Xero access_token is required")
        if not self._tenant_id:
            raise ValueError("Xero tenant_id is required")
        return httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Xero-Tenant-Id": self._tenant_id,
            },
            timeout=30.0,
        )

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:

            if action_name == "list-contacts":
                params: Dict[str, Any] = {}
                if payload.get("page"):
                    params["page"] = payload["page"]
                if payload.get("where"):
                    params["where"] = payload["where"]
                if payload.get("include_archived"):
                    params["includeArchived"] = "true"
                response = await client.get("/Contacts", params=params)
                response.raise_for_status()
                return response.json().get("Contacts", [])

            if action_name == "create-contact":
                contact: Dict[str, Any] = {"Name": payload["name"]}
                if payload.get("email"):
                    contact["EmailAddress"] = payload["email"]
                if payload.get("phone"):
                    contact["Phones"] = [
                        {"PhoneType": "DEFAULT", "PhoneNumber": payload["phone"]}
                    ]
                if payload.get("is_customer") is not None:
                    contact["IsCustomer"] = payload["is_customer"]
                if payload.get("is_supplier") is not None:
                    contact["IsSupplier"] = payload["is_supplier"]
                response = await client.put("/Contacts", json={"Contacts": [contact]})
                response.raise_for_status()
                contacts = response.json().get("Contacts", [])
                return contacts[0] if contacts else response.json()

            if action_name == "update-contact":
                contact = {"Name": payload.get("name", "")}
                if payload.get("email"):
                    contact["EmailAddress"] = payload["email"]
                if payload.get("phone"):
                    contact["Phones"] = [
                        {"PhoneType": "DEFAULT", "PhoneNumber": payload["phone"]}
                    ]
                response = await client.post(
                    f"/Contacts/{payload['contact_id']}", json=contact
                )
                response.raise_for_status()
                contacts = response.json().get("Contacts", [])
                return contacts[0] if contacts else response.json()

            if action_name == "create-invoice":
                line_items: List[Dict] = [
                    {
                        "Description": item.get("description", ""),
                        "Quantity": item.get("quantity", 1),
                        "UnitAmount": item["unit_amount"],
                        "AccountCode": item.get("account_code", "200"),
                        **({"TaxType": item["tax_type"]} if item.get("tax_type") else {}),
                    }
                    for item in payload.get("line_items", [])
                ]
                invoice: Dict[str, Any] = {
                    "Type": payload.get("type", "ACCREC"),
                    "Contact": {"ContactID": payload["contact_id"]},
                    "LineItems": line_items,
                }
                if payload.get("due_date"):
                    invoice["DueDate"] = payload["due_date"]
                if payload.get("invoice_number"):
                    invoice["InvoiceNumber"] = payload["invoice_number"]
                if payload.get("status"):
                    invoice["Status"] = payload["status"]
                if payload.get("reference"):
                    invoice["Reference"] = payload["reference"]
                response = await client.put("/Invoices", json={"Invoices": [invoice]})
                response.raise_for_status()
                invoices = response.json().get("Invoices", [])
                return invoices[0] if invoices else response.json()

            if action_name == "list-invoices":
                params = {}
                if payload.get("page"):
                    params["page"] = payload["page"]
                if payload.get("status"):
                    params["Statuses"] = payload["status"]
                if payload.get("contact_id"):
                    params["ContactIDs"] = payload["contact_id"]
                response = await client.get("/Invoices", params=params)
                response.raise_for_status()
                return response.json().get("Invoices", [])

            if action_name == "get-invoice":
                invoice_id = payload["invoice_id"]
                response = await client.get(f"/Invoices/{invoice_id}")
                response.raise_for_status()
                invoices = response.json().get("Invoices", [])
                return invoices[0] if invoices else response.json()

            if action_name == "send-invoice":
                invoice_id = payload["invoice_id"]
                body: Dict[str, Any] = {}
                if payload.get("email"):
                    body["EmailAddress"] = payload["email"]
                response = await client.post(
                    f"/Invoices/{invoice_id}/Email", json=body
                )
                response.raise_for_status()
                return {"invoice_id": invoice_id, "status": "sent"}

            if action_name == "create-payment":
                payment: Dict[str, Any] = {
                    "Invoice": {"InvoiceID": payload["invoice_id"]},
                    "Account": {"AccountID": payload["account_id"]},
                    "Amount": payload["amount"],
                }
                if payload.get("date"):
                    payment["Date"] = payload["date"]
                if payload.get("reference"):
                    payment["Reference"] = payload["reference"]
                response = await client.put(
                    "/Payments", json={"Payments": [payment]}
                )
                response.raise_for_status()
                payments = response.json().get("Payments", [])
                return payments[0] if payments else response.json()

            if action_name == "list-payments":
                params = {}
                if payload.get("page"):
                    params["page"] = payload["page"]
                if payload.get("status"):
                    params["Statuses"] = payload["status"]
                response = await client.get("/Payments", params=params)
                response.raise_for_status()
                return response.json().get("Payments", [])

            if action_name == "list-accounts":
                params = {}
                if payload.get("type"):
                    params["where"] = f'Type=="{payload["type"]}"'
                response = await client.get("/Accounts", params=params)
                response.raise_for_status()
                return response.json().get("Accounts", [])

            if action_name == "get-balance-sheet":
                params = {}
                if payload.get("date"):
                    params["date"] = payload["date"]
                if payload.get("periods"):
                    params["periods"] = payload["periods"]
                if payload.get("timeframe"):
                    params["timeframe"] = payload["timeframe"]
                response = await client.get("/Reports/BalanceSheet", params=params)
                response.raise_for_status()
                reports = response.json().get("Reports", [])
                return reports[0] if reports else response.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "xero"}
