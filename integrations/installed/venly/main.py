"""Auto-generated integration for Venly."""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate



class IntegrationLogic(BaseIntegrationTemplate):
    """Integration for Venly (oauth2)."""

    BASE_URL = "https://api.venly.io"

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
            if sync_name == "nft_sync":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            elif sync_name == "transaction_sync":
                r = await client.get("/")
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        async with self._client() as client:
            if action_name == "get-nft":
                nft_id = payload.get("nft_id")
                if not nft_id:
                    raise ValueError("'nft_id' required")
                r = await client.get(f"/nfts/{nft_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-nfts":
                wallet_address = payload.get("wallet_address")
                if not wallet_address:
                    raise ValueError("'wallet_address' required")
                params = {k: v for k, v in payload.items() if k not in ['wallet_address'] and v is not None}
                r = await client.get(f"/wallets/{wallet_address}/nfts", params=params)
                r.raise_for_status()
                return r.json()
            elif action_name == "create-offer":
                body = {k: v for k, v in payload.items() if k not in [] and v is not None}
                r = await client.post("/offers", json=body)
                r.raise_for_status()
                return r.json()
            elif action_name == "accept-offer":
                offer_id = payload.get("offer_id")
                if not offer_id:
                    raise ValueError("'offer_id' required")
                r = await client.post(f"/offers/{offer_id}/accept")
                r.raise_for_status()
                return r.json()
            elif action_name == "cancel-offer":
                offer_id = payload.get("offer_id")
                if not offer_id:
                    raise ValueError("'offer_id' required")
                r = await client.post(f"/offers/{offer_id}/cancel")
                r.raise_for_status()
                return r.json()
            elif action_name == "get-transaction":
                transaction_id = payload.get("transaction_id")
                if not transaction_id:
                    raise ValueError("'transaction_id' required")
                r = await client.get(f"/transactions/{transaction_id}")
                r.raise_for_status()
                return r.json()
            elif action_name == "list-transactions":
                wallet_address = payload.get("wallet_address")
                if not wallet_address:
                    raise ValueError("'wallet_address' required")
                params = {k: v for k, v in payload.items() if k not in ['wallet_address'] and v is not None}
                r = await client.get(f"/wallets/{wallet_address}/transactions", params=params)
                r.raise_for_status()
                return r.json()
            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "venly"}
