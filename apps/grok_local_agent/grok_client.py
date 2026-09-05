import os
from datetime import datetime, timezone

import httpx

from .config import XAI_API_BASE, XAI_MODEL, offline_mode


class GrokClientError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY") or ""
    key = key.strip().strip('"').strip("'")
    if not key:
        raise GrokClientError("XAI_API_KEY is not configured")
    return key


def _looks_like_xai_key(key: str) -> bool:
    return key.startswith("xai-") and len(key) > 12


def chat(message: str, model: str | None = None) -> dict:
    if not message or not message.strip():
        raise ValueError("message is required")

    chosen_model = model or XAI_MODEL
    if offline_mode():
        return {
            "model": f"{chosen_model}-offline",
            "mode": "offline",
            "content": (
                "Offline Grok agent received: "
                + message.strip()
                + ". Live API is disabled. Set WARLOCK_GROK_OFFLINE=0 and a valid xai- key to call api.x.ai."
            ),
            "raw_id": "offline-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        }

    key = _api_key()
    if not _looks_like_xai_key(key):
        raise GrokClientError(
            "XAI_API_KEY is not an xAI key. Expected a key starting with xai- from https://console.x.ai"
        )

    payload = {
        "model": chosen_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are the Warlock Grok Agent. "
                    "Do not modify the original ChatGPT local agent."
                ),
            },
            {"role": "user", "content": message.strip()},
        ],
    }

    response = httpx.post(
        f"{XAI_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    text = response.text[:400].replace(key, "[redacted]")
    if response.status_code >= 400:
        raise GrokClientError(f"Grok API {response.status_code}: {text}")

    data = response.json()
    choices = data.get("choices") or []
    content = ""
    if choices:
        content = choices[0].get("message", {}).get("content") or ""

    return {
        "model": payload["model"],
        "mode": "live",
        "content": content,
        "raw_id": data.get("id"),
    }
