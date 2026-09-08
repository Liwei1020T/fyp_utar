from __future__ import annotations

import json
from urllib import request as urllib_request


def get_openwa_session_state(
    *,
    endpoint: str,
    api_key: str | None,
) -> dict[str, object]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    http_request = urllib_request.Request(endpoint, headers=headers, method="GET")
    with urllib_request.urlopen(http_request, timeout=5) as response:
        provider_response = json.loads(response.read().decode("utf-8"))
    if not isinstance(provider_response, dict):
        raise ValueError("OpenWA returned an invalid session response")
    return provider_response


def openwa_session_pause_reason(session_state: dict[str, object]) -> str | None:
    restriction = session_state.get("restriction")
    if restriction:
        kind = (
            restriction.get("kind") if isinstance(restriction, dict) else "restricted"
        )
        return f"OpenWA session restricted ({kind or 'restricted'}); delivery paused"

    session_status = str(session_state.get("status") or "").strip().lower()
    if session_status not in {"ready", "connected"}:
        return f"OpenWA session is {session_status or 'unavailable'}; delivery paused"
    return None


def send_openwa_text(
    *,
    endpoint: str,
    api_key: str | None,
    chat_id: str,
    text: str,
) -> str:
    body = json.dumps({"chatId": chat_id, "text": text}).encode("utf-8")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    request = urllib_request.Request(
        endpoint, data=body, headers=headers, method="POST"
    )
    with urllib_request.urlopen(request, timeout=5) as response:
        provider_response = json.loads(response.read().decode("utf-8"))
    if not isinstance(provider_response, dict):
        raise ValueError("OpenWA returned an invalid response")
    provider_message = (
        provider_response.get("messageId")
        or provider_response.get("id")
        or "OpenWA accepted"
    )
    return str(provider_message)
