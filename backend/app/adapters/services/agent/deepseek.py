from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

from app.shared.errors import ServiceUnavailableError


@dataclass(frozen=True)
class DeepSeekAgentClient:
    api_key: str
    model: str
    base_url: str
    timeout_seconds: float

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, object]],
        tool_choice: str,
        user_id: str,
    ) -> dict[str, Any]:
        payload: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 1600,
            "user_id": user_id,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        for attempt in range(2):
            if attempt:
                payload["messages"] = [
                    *messages,
                    {
                        "role": "user",
                        "content": (
                            "Return one non-empty JSON object matching the requested "
                            "schema. Use this only as a format example: "
                            '{"answer":"Plain response.","summary":"Short summary.",'
                            '"evidence":[],"evidence_status":"insufficient_evidence",'
                            '"suggested_questions":[],"suggested_actions":[],'
                            '"handoff":null}'
                        ),
                    },
                ]
            request = Request(
                f"{self.base_url.rstrip('/')}/chat/completions",
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
            except (HTTPError, URLError, TimeoutError, OSError) as error:
                raise ServiceUnavailableError("Agent model is unavailable") from error

            try:
                result = json.loads(body)
            except json.JSONDecodeError as error:
                raise ServiceUnavailableError(
                    "Agent model returned an invalid response"
                ) from error
            if not isinstance(result, dict):
                raise ServiceUnavailableError(
                    "Agent model returned an invalid response"
                )

            choices = result.get("choices")
            message = (
                choices[0].get("message")
                if isinstance(choices, list)
                and choices
                and isinstance(choices[0], dict)
                else None
            )
            content = message.get("content") if isinstance(message, dict) else None
            if (
                attempt == 0
                and isinstance(message, dict)
                and not message.get("tool_calls")
                and (
                    content is None
                    or (isinstance(content, str) and not content.strip())
                )
            ):
                continue
            return result

        raise ServiceUnavailableError("Agent model returned an empty response")
