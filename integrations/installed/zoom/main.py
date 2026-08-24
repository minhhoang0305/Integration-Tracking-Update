import httpx
from typing import Any, Dict, Optional
from app.integrations.base import BaseIntegrationTemplate


class IntegrationLogic(BaseIntegrationTemplate):
    BASE_URL = "https://api.zoom.us/v2"

    def __init__(self) -> None:
        self._token: Optional[str] = None

    async def initialize(self, credentials_dict: Dict[str, Any], connection_config: Optional[Dict[str, Any]] = None) -> None:
        self._token = credentials_dict.get("access_token")

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.BASE_URL, headers=self._headers(), timeout=30.0)

    async def execute_sync_task(self, sync_name: str = "default", **kwargs) -> Any:
        raise ValueError(f"Unsupported sync: {sync_name}")

    async def execute_action(self, action_name: str, payload: Dict[str, Any]) -> Any:  # noqa: C901
        async with self._client() as client:

            # ── Group 1: Meetings ─────────────────────────────────────────────
            if action_name == "list-meetings":
                user_id = payload.get("userId", "me")
                params = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.get(f"/users/{user_id}/meetings", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-meeting":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.get(f"/meetings/{meeting_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-meeting":
                if not payload.get("topic"):
                    raise ValueError("'topic' is required")
                user_id = payload.get("userId", "me")
                body = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.post(f"/users/{user_id}/meetings", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-meeting":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                body = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.patch(f"/meetings/{meeting_id}", json=body)
                r.raise_for_status()
                return r.json() if r.content else {"status": "updated"}

            elif action_name == "delete-meeting":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.delete(f"/meetings/{meeting_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "end-meeting":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.put(f"/meetings/{meeting_id}/status", json={"action": "end"})
                r.raise_for_status()
                return {"status": "ended"}

            elif action_name == "recover-meeting":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.put(f"/meetings/{meeting_id}/status", json={"action": "recover"})
                r.raise_for_status()
                return {"status": "recovered"}

            elif action_name == "get-meeting-invitation":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.get(f"/meetings/{meeting_id}/invitation")
                r.raise_for_status()
                return r.json()

            elif action_name == "get-meeting-summary":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.get(f"/meetings/{meeting_id}/summary")
                r.raise_for_status()
                return r.json()

            # ── Group 2: Meeting Registrants ──────────────────────────────────
            elif action_name == "list-meeting-registrants":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                params = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.get(f"/meetings/{meeting_id}/registrants", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "add-meeting-registrant":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                body = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.post(f"/meetings/{meeting_id}/registrants", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-meeting-registrant-status":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                body = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.put(f"/meetings/{meeting_id}/registrants/status", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-meeting-registrant":
                meeting_id = payload.get("meetingId")
                registrant_id = payload.get("registrantId")
                if not meeting_id or not registrant_id:
                    raise ValueError("'meetingId' and 'registrantId' are required")
                r = await client.delete(f"/meetings/{meeting_id}/registrants/{registrant_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "get-meeting-registrant":
                meeting_id = payload.get("meetingId")
                registrant_id = payload.get("registrantId")
                if not meeting_id or not registrant_id:
                    raise ValueError("'meetingId' and 'registrantId' are required")
                r = await client.get(f"/meetings/{meeting_id}/registrants/{registrant_id}")
                r.raise_for_status()
                return r.json()

            # ── Group 3: Meeting Polls ────────────────────────────────────────
            elif action_name == "list-meeting-polls":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.get(f"/meetings/{meeting_id}/polls")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-meeting-poll":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                body = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.post(f"/meetings/{meeting_id}/polls", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-meeting-poll":
                meeting_id = payload.get("meetingId")
                poll_id = payload.get("pollId")
                if not meeting_id or not poll_id:
                    raise ValueError("'meetingId' and 'pollId' are required")
                r = await client.get(f"/meetings/{meeting_id}/polls/{poll_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "update-meeting-poll":
                meeting_id = payload.get("meetingId")
                poll_id = payload.get("pollId")
                if not meeting_id or not poll_id:
                    raise ValueError("'meetingId' and 'pollId' are required")
                body = {k: v for k, v in payload.items() if k not in ("meetingId", "pollId") and v is not None}
                r = await client.put(f"/meetings/{meeting_id}/polls/{poll_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-meeting-poll":
                meeting_id = payload.get("meetingId")
                poll_id = payload.get("pollId")
                if not meeting_id or not poll_id:
                    raise ValueError("'meetingId' and 'pollId' are required")
                r = await client.delete(f"/meetings/{meeting_id}/polls/{poll_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            # ── Group 4: Meeting Participants ─────────────────────────────────
            elif action_name == "list-meeting-participants":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                params = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.get(f"/report/meetings/{meeting_id}/participants", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-past-meeting-participants":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                params = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.get(f"/past_meetings/{meeting_id}/participants", params=params)
                r.raise_for_status()
                return r.json()

            # ── Group 5: Recordings ───────────────────────────────────────────
            elif action_name == "list-recordings":
                user_id = payload.get("userId", "me")
                params = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.get(f"/users/{user_id}/recordings", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-recording":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.get(f"/meetings/{meeting_id}/recordings")
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-recording":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                params = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.delete(f"/meetings/{meeting_id}/recordings", params=params)
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "delete-recording-file":
                meeting_id = payload.get("meetingId")
                recording_id = payload.get("recordingId")
                if not meeting_id or not recording_id:
                    raise ValueError("'meetingId' and 'recordingId' are required")
                r = await client.delete(f"/meetings/{meeting_id}/recordings/{recording_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "get-recording-settings":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.get(f"/meetings/{meeting_id}/recordings/settings")
                r.raise_for_status()
                return r.json()

            elif action_name == "update-recording-settings":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                body = {k: v for k, v in payload.items() if k != "meetingId" and v is not None}
                r = await client.patch(f"/meetings/{meeting_id}/recordings/settings", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "recover-recording":
                meeting_id = payload.get("meetingId")
                if not meeting_id:
                    raise ValueError("'meetingId' is required")
                r = await client.put(f"/meetings/{meeting_id}/recordings/status", json={"action": "recover"})
                r.raise_for_status()
                return {"status": "recovered"}

            # ── Group 6: Webinars ─────────────────────────────────────────────
            elif action_name == "list-webinars":
                user_id = payload.get("userId", "me")
                params = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.get(f"/users/{user_id}/webinars", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-webinar":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                r = await client.get(f"/webinars/{webinar_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-webinar":
                if not payload.get("topic"):
                    raise ValueError("'topic' is required")
                user_id = payload.get("userId", "me")
                body = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.post(f"/users/{user_id}/webinars", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-webinar":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                body = {k: v for k, v in payload.items() if k != "webinarId" and v is not None}
                r = await client.patch(f"/webinars/{webinar_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-webinar":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                r = await client.delete(f"/webinars/{webinar_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "get-webinar-invitation":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                r = await client.get(f"/webinars/{webinar_id}/invitation")
                r.raise_for_status()
                return r.json()

            # ── Group 7: Webinar Registrants ──────────────────────────────────
            elif action_name == "list-webinar-registrants":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                params = {k: v for k, v in payload.items() if k != "webinarId" and v is not None}
                r = await client.get(f"/webinars/{webinar_id}/registrants", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "add-webinar-registrant":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                body = {k: v for k, v in payload.items() if k != "webinarId" and v is not None}
                r = await client.post(f"/webinars/{webinar_id}/registrants", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-webinar-registrant-status":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                body = {k: v for k, v in payload.items() if k != "webinarId" and v is not None}
                r = await client.put(f"/webinars/{webinar_id}/registrants/status", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-webinar-registrant":
                webinar_id = payload.get("webinarId")
                registrant_id = payload.get("registrantId")
                if not webinar_id or not registrant_id:
                    raise ValueError("'webinarId' and 'registrantId' are required")
                r = await client.delete(f"/webinars/{webinar_id}/registrants/{registrant_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            # ── Group 8: Webinar Panelists ────────────────────────────────────
            elif action_name == "list-webinar-panelists":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                r = await client.get(f"/webinars/{webinar_id}/panelists")
                r.raise_for_status()
                return r.json()

            elif action_name == "add-webinar-panelist":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                body = {k: v for k, v in payload.items() if k != "webinarId" and v is not None}
                r = await client.post(f"/webinars/{webinar_id}/panelists", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-webinar-panelist":
                webinar_id = payload.get("webinarId")
                panelist_id = payload.get("panelistId")
                if not webinar_id or not panelist_id:
                    raise ValueError("'webinarId' and 'panelistId' are required")
                r = await client.delete(f"/webinars/{webinar_id}/panelists/{panelist_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            # ── Group 9: Webinar Polls ────────────────────────────────────────
            elif action_name == "list-webinar-polls":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                r = await client.get(f"/webinars/{webinar_id}/polls")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-webinar-poll":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                body = {k: v for k, v in payload.items() if k != "webinarId" and v is not None}
                r = await client.post(f"/webinars/{webinar_id}/polls", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-webinar-poll":
                webinar_id = payload.get("webinarId")
                poll_id = payload.get("pollId")
                if not webinar_id or not poll_id:
                    raise ValueError("'webinarId' and 'pollId' are required")
                r = await client.get(f"/webinars/{webinar_id}/polls/{poll_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "update-webinar-poll":
                webinar_id = payload.get("webinarId")
                poll_id = payload.get("pollId")
                if not webinar_id or not poll_id:
                    raise ValueError("'webinarId' and 'pollId' are required")
                body = {k: v for k, v in payload.items() if k not in ("webinarId", "pollId") and v is not None}
                r = await client.put(f"/webinars/{webinar_id}/polls/{poll_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-webinar-poll":
                webinar_id = payload.get("webinarId")
                poll_id = payload.get("pollId")
                if not webinar_id or not poll_id:
                    raise ValueError("'webinarId' and 'pollId' are required")
                r = await client.delete(f"/webinars/{webinar_id}/polls/{poll_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            # ── Group 10: Users ───────────────────────────────────────────────
            elif action_name == "list-users":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/users", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-user":
                user_id = payload.get("userId", "me")
                r = await client.get(f"/users/{user_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-user":
                if not payload.get("email"):
                    raise ValueError("'email' is required")
                r = await client.post("/users", json={"action": payload.get("action", "create"), "user_info": payload})
                r.raise_for_status()
                return r.json()

            elif action_name == "update-user":
                user_id = payload.get("userId", "me")
                body = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.patch(f"/users/{user_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-user":
                user_id = payload.get("userId")
                if not user_id:
                    raise ValueError("'userId' is required")
                params = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.delete(f"/users/{user_id}", params=params)
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "get-user-settings":
                user_id = payload.get("userId", "me")
                r = await client.get(f"/users/{user_id}/settings")
                r.raise_for_status()
                return r.json()

            elif action_name == "update-user-settings":
                user_id = payload.get("userId", "me")
                body = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.patch(f"/users/{user_id}/settings", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "get-user-token":
                user_id = payload.get("userId", "me")
                params = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.get(f"/users/{user_id}/token", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "revoke-user-token":
                user_id = payload.get("userId", "me")
                r = await client.delete(f"/users/{user_id}/token")
                r.raise_for_status()
                return {"status": "revoked"}

            elif action_name == "list-user-assistants":
                user_id = payload.get("userId", "me")
                r = await client.get(f"/users/{user_id}/assistants")
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-user-assistant":
                user_id = payload.get("userId", "me")
                assistant_id = payload.get("assistantId")
                if not assistant_id:
                    raise ValueError("'assistantId' is required")
                r = await client.delete(f"/users/{user_id}/assistants/{assistant_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            # ── Group 11: Groups ──────────────────────────────────────────────
            elif action_name == "list-groups":
                r = await client.get("/groups")
                r.raise_for_status()
                return r.json()

            elif action_name == "get-group":
                group_id = payload.get("groupId")
                if not group_id:
                    raise ValueError("'groupId' is required")
                r = await client.get(f"/groups/{group_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-group":
                if not payload.get("name"):
                    raise ValueError("'name' is required")
                r = await client.post("/groups", json=payload)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-group":
                group_id = payload.get("groupId")
                if not group_id:
                    raise ValueError("'groupId' is required")
                body = {k: v for k, v in payload.items() if k != "groupId" and v is not None}
                r = await client.patch(f"/groups/{group_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-group":
                group_id = payload.get("groupId")
                if not group_id:
                    raise ValueError("'groupId' is required")
                r = await client.delete(f"/groups/{group_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "list-group-members":
                group_id = payload.get("groupId")
                if not group_id:
                    raise ValueError("'groupId' is required")
                params = {k: v for k, v in payload.items() if k != "groupId" and v is not None}
                r = await client.get(f"/groups/{group_id}/members", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "add-group-members":
                group_id = payload.get("groupId")
                if not group_id:
                    raise ValueError("'groupId' is required")
                body = {"members": payload.get("members", [])}
                r = await client.post(f"/groups/{group_id}/members", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "delete-group-member":
                group_id = payload.get("groupId")
                member_id = payload.get("memberId")
                if not group_id or not member_id:
                    raise ValueError("'groupId' and 'memberId' are required")
                r = await client.delete(f"/groups/{group_id}/members/{member_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "list-group-admins":
                group_id = payload.get("groupId")
                if not group_id:
                    raise ValueError("'groupId' is required")
                params = {k: v for k, v in payload.items() if k != "groupId" and v is not None}
                r = await client.get(f"/groups/{group_id}/admins", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "add-group-admin":
                group_id = payload.get("groupId")
                if not group_id:
                    raise ValueError("'groupId' is required")
                body = {"admins": payload.get("admins", [])}
                r = await client.post(f"/groups/{group_id}/admins", json=body)
                r.raise_for_status()
                return r.json()

            # ── Group 12: Accounts ────────────────────────────────────────────
            elif action_name == "get-account":
                account_id = payload.get("accountId", "me")
                r = await client.get(f"/accounts/{account_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "update-account":
                account_id = payload.get("accountId", "me")
                body = {k: v for k, v in payload.items() if k != "accountId" and v is not None}
                r = await client.patch(f"/accounts/{account_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "get-account-settings":
                account_id = payload.get("accountId", "me")
                params = {k: v for k, v in payload.items() if k != "accountId" and v is not None}
                r = await client.get(f"/accounts/{account_id}/settings", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-account-settings":
                account_id = payload.get("accountId", "me")
                body = {k: v for k, v in payload.items() if k != "accountId" and v is not None}
                r = await client.patch(f"/accounts/{account_id}/settings", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "get-account-plans":
                account_id = payload.get("accountId", "me")
                r = await client.get(f"/accounts/{account_id}/plans")
                r.raise_for_status()
                return r.json()

            # ── Group 13: Reports ─────────────────────────────────────────────
            elif action_name == "get-daily-usage-report":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/report/daily", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-active-inactive-hosts-report":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/report/users", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-webinar-participants-report":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                params = {k: v for k, v in payload.items() if k != "webinarId" and v is not None}
                r = await client.get(f"/report/webinars/{webinar_id}/participants", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-telephone-report":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/report/telephone", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-cloud-recording-report":
                user_id = payload.get("userId", "me")
                params = {k: v for k, v in payload.items() if k != "userId" and v is not None}
                r = await client.get(f"/report/cloud_recording", params=params)
                r.raise_for_status()
                return r.json()

            # ── Group 14: Chat Channels ───────────────────────────────────────
            elif action_name == "list-chat-channels":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/chat/users/me/channels", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "create-chat-channel":
                if not payload.get("name"):
                    raise ValueError("'name' is required")
                r = await client.post("/chat/users/me/channels", json=payload)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-chat-channel":
                channel_id = payload.get("channelId")
                if not channel_id:
                    raise ValueError("'channelId' is required")
                r = await client.get(f"/chat/channels/{channel_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "update-chat-channel":
                channel_id = payload.get("channelId")
                if not channel_id:
                    raise ValueError("'channelId' is required")
                body = {k: v for k, v in payload.items() if k != "channelId" and v is not None}
                r = await client.patch(f"/chat/channels/{channel_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-chat-channel":
                channel_id = payload.get("channelId")
                if not channel_id:
                    raise ValueError("'channelId' is required")
                r = await client.delete(f"/chat/channels/{channel_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "list-chat-messages":
                to_channel = payload.get("to_channel")
                to_contact = payload.get("to_contact")
                if not to_channel and not to_contact:
                    raise ValueError("'to_channel' or 'to_contact' is required")
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/chat/users/me/messages", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "send-chat-message":
                if not payload.get("message"):
                    raise ValueError("'message' is required")
                r = await client.post("/chat/users/me/messages", json=payload)
                r.raise_for_status()
                return r.json()

            # ── Group 15: Zoom Rooms ──────────────────────────────────────────
            elif action_name == "list-zoom-rooms":
                params = {k: v for k, v in payload.items() if v is not None}
                r = await client.get("/rooms", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "get-zoom-room":
                room_id = payload.get("roomId")
                if not room_id:
                    raise ValueError("'roomId' is required")
                r = await client.get(f"/rooms/{room_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-zoom-room":
                if not payload.get("name"):
                    raise ValueError("'name' is required")
                r = await client.post("/rooms", json=payload)
                r.raise_for_status()
                return r.json()

            elif action_name == "update-zoom-room":
                room_id = payload.get("roomId")
                if not room_id:
                    raise ValueError("'roomId' is required")
                body = {k: v for k, v in payload.items() if k != "roomId" and v is not None}
                r = await client.patch(f"/rooms/{room_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-zoom-room":
                room_id = payload.get("roomId")
                if not room_id:
                    raise ValueError("'roomId' is required")
                r = await client.delete(f"/rooms/{room_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            # ── Group 16: Chat Message extras ─────────────────────────────────
            elif action_name == "update-chat-message":
                message_id = payload.get("messageId")
                if not message_id:
                    raise ValueError("'messageId' is required")
                body = {k: v for k, v in payload.items() if k != "messageId" and v is not None}
                r = await client.put(f"/chat/users/me/messages/{message_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-chat-message":
                message_id = payload.get("messageId")
                if not message_id:
                    raise ValueError("'messageId' is required")
                params = {k: v for k, v in payload.items() if k != "messageId" and v is not None}
                r = await client.delete(f"/chat/users/me/messages/{message_id}", params=params)
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "list-chat-channel-members":
                channel_id = payload.get("channelId")
                if not channel_id:
                    raise ValueError("'channelId' is required")
                params = {k: v for k, v in payload.items() if k != "channelId" and v is not None}
                r = await client.get(f"/chat/channels/{channel_id}/members", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "add-chat-channel-member":
                channel_id = payload.get("channelId")
                if not channel_id:
                    raise ValueError("'channelId' is required")
                body = {"members": payload.get("members", [])}
                r = await client.post(f"/chat/channels/{channel_id}/members", json=body)
                r.raise_for_status()
                return r.json()

            elif action_name == "remove-chat-channel-member":
                channel_id = payload.get("channelId")
                member_id = payload.get("memberId")
                if not channel_id or not member_id:
                    raise ValueError("'channelId' and 'memberId' are required")
                r = await client.delete(f"/chat/channels/{channel_id}/members/{member_id}")
                r.raise_for_status()
                return {"status": "removed"}

            # ── Group 17: Roles ───────────────────────────────────────────────
            elif action_name == "list-roles":
                r = await client.get("/roles")
                r.raise_for_status()
                return r.json()

            elif action_name == "create-role":
                if not payload.get("name"):
                    raise ValueError("'name' is required")
                r = await client.post("/roles", json={k: v for k, v in payload.items() if v is not None})
                r.raise_for_status()
                return r.json()

            elif action_name == "get-role":
                role_id = payload.get("roleId")
                if not role_id:
                    raise ValueError("'roleId' is required")
                r = await client.get(f"/roles/{role_id}")
                r.raise_for_status()
                return r.json()

            elif action_name == "update-role":
                role_id = payload.get("roleId")
                if not role_id:
                    raise ValueError("'roleId' is required")
                body = {k: v for k, v in payload.items() if k != "roleId" and v is not None}
                r = await client.patch(f"/roles/{role_id}", json=body)
                r.raise_for_status()
                return {"status": "updated"}

            elif action_name == "delete-role":
                role_id = payload.get("roleId")
                if not role_id:
                    raise ValueError("'roleId' is required")
                r = await client.delete(f"/roles/{role_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            elif action_name == "list-role-members":
                role_id = payload.get("roleId")
                if not role_id:
                    raise ValueError("'roleId' is required")
                params = {k: v for k, v in payload.items() if k != "roleId" and v is not None}
                r = await client.get(f"/roles/{role_id}/members", params=params)
                r.raise_for_status()
                return r.json()

            elif action_name == "add-role-members":
                role_id = payload.get("roleId")
                if not role_id:
                    raise ValueError("'roleId' is required")
                body = {"members": payload.get("members", [])}
                r = await client.post(f"/roles/{role_id}/members", json=body)
                r.raise_for_status()
                return r.json()

            # ── Group 18: Group Admin extras ──────────────────────────────────
            elif action_name == "delete-group-admin":
                group_id = payload.get("groupId")
                admin_id = payload.get("adminId")
                if not group_id or not admin_id:
                    raise ValueError("'groupId' and 'adminId' are required")
                r = await client.delete(f"/groups/{group_id}/admins/{admin_id}")
                r.raise_for_status()
                return {"status": "deleted"}

            # ── Group 19: User Assistant extras ───────────────────────────────
            elif action_name == "add-user-assistant":
                user_id = payload.get("userId", "me")
                body = {"assistants": payload.get("assistants", [])}
                r = await client.post(f"/users/{user_id}/assistants", json=body)
                r.raise_for_status()
                return r.json()

            # ── Group 20: Report extras ───────────────────────────────────────
            elif action_name == "get-webinar-detail-report":
                webinar_id = payload.get("webinarId")
                if not webinar_id:
                    raise ValueError("'webinarId' is required")
                r = await client.get(f"/report/webinars/{webinar_id}")
                r.raise_for_status()
                return r.json()

            raise ValueError(f"Unknown action: {action_name}")

    async def handle_webhook(self, request: Any) -> Any:
        return {"status": "ok", "provider": "zoom"}
