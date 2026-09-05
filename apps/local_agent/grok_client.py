import os

import httpx

from .config import XAI_API_BASE, XAI_MODEL


class GrokClientError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    if not key:
        raise GrokClientError("XAI_API_KEY is not configured")
    return key


def chat(message: str, model: str | None = None) -> dict:
    if not message or not message.strip():
        raise ValueError("message is required")

    payload = {
        "model": model or XAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the Warlock Local Agent assistant. "
                    "Operate only within the Warlock Plugins Factory workspace."
                ),
            },
            {"role": "user", "content": message.strip()},
        ],
    }

    response = httpx.post(
        f"{XAI_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    if response.status_code >= 400:
        raise GrokClientError(
            f"Grok API error {response.status_code}: {response.text[:500]}"
        )

    data = response.json()
    choices = data.get("choices") or []
    content = ""
    if choices:
        content = (
            choices[0].get("message", {}).get("content")
            or ""
        )

    return {
        "model": payload["model"],
        "content": content,
        "raw_id": data.get("id"),
    }
