from __future__ import annotations

import json
from urllib import request as urllib_request


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
