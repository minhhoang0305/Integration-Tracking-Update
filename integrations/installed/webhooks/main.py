"""Universal Webhooks / HTTP Requests integration.

This is a special "meta-integration" that allows sending HTTP requests
to any URL. It acts as a universal interoperability layer — users can
connect to services that don't have a dedicated integration yet.
"""

import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    """Universal HTTP connector — send requests to any URL."""

    def __init__(self) -> None:
        self._auth_header: Optional[str] = None
        self._base_url: Optional[str] = None

    async def initialize(
        self,
        credentials_dict: Dict[str, Any],
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._auth_header = (
            credentials_dict.get("api_key")
            or credentials_dict.get("apiKey")
            or (connection_config or {}).get("api_key")
        )
        self._base_url = (connection_config or {}).get("base_url", "")

    def _resolve_url(self, url: str) -> str:
        """Resolve URL: use as-is if absolute, prepend base_url if relative."""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        base = (self._base_url or "").rstrip("/")
        if base:
            return f"{base}/{url.lstrip('/')}"
        return url

    def _build_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._auth_header:
            headers["Authorization"] = self._auth_header
        if custom_headers:
            headers.update(custom_headers)
        return headers

    async def _do_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        body: Optional[Dict] = None,
        query_params: Optional[Dict] = None,
        form_data: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        resolved_url = self._resolve_url(url)
        req_headers = self._build_headers(headers)

        if form_data is not None:
            req_headers.pop("Content-Type", None)

        async with httpx.AsyncClient(timeout=float(timeout)) as client:
            r = await client.request(
                method=method.upper(),
                url=resolved_url,
                headers=req_headers,
                json=body if body and not form_data else None,
                data=form_data,
                params=query_params,
            )
            # Try JSON, fall back to text
            try:
                resp_body = r.json()
            except Exception:
                resp_body = r.text

            return {
                "status_code": r.status_code,
                "headers": dict(r.headers),
                "body": resp_body,
            }

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        if sync_name == "sync-poll-endpoint":
            url = kwargs.get("url") or (self._base_url or "")
            if not url:
                raise ValueError("No URL configured for polling. Set base_url in connection_config or pass url kwarg.")
            return await self._do_request("GET", url)
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:
        url = payload.get("url", "")
        headers = payload.get("headers")
        body = payload.get("body")
        query_params = payload.get("query_params")
        form_data = payload.get("form_data")
        timeout = payload.get("timeout", 30)

        if action_name == "http-request":
            method = payload.get("method", "GET")
            if not url:
                raise ValueError("'url' required")
            return await self._do_request(method, url, headers, body, query_params, timeout=timeout)

        elif action_name == "http-get":
            if not url:
                raise ValueError("'url' required")
            return await self._do_request("GET", url, headers, query_params=query_params, timeout=timeout)

        elif action_name == "http-post":
            if not url:
                raise ValueError("'url' required")
            return await self._do_request("POST", url, headers, body, query_params, timeout=timeout)

        elif action_name == "http-put":
            if not url:
                raise ValueError("'url' required")
            return await self._do_request("PUT", url, headers, body, timeout=timeout)

        elif action_name == "http-delete":
            if not url:
                raise ValueError("'url' required")
            return await self._do_request("DELETE", url, headers, query_params=query_params, timeout=timeout)

        elif action_name == "http-form-post":
            if not url or not form_data:
                raise ValueError("'url' and 'form_data' required")
            return await self._do_request("POST", url, headers, form_data=form_data, timeout=timeout)

        raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "webhooks"}
