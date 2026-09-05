import os

import httpx

from .brain import answer, reply as offline_reply
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


LOCAL_HINTS = (
    "thall", "djent", "doom", "preset", "adaa", "oversample", "gate",
    "morph", "dsp", "black metal", "ambient", "architecture", "قانون",
    "پریست", "تون", "stack", "sqlite", "checkpoint",
)


def _local_first(message: str) -> bool:
    key = message.lower()
    if offline_mode():
        return True
    return any(h in key for h in LOCAL_HINTS)


def chat(message: str, model: str | None = None) -> dict:
    if not message or not message.strip():
        raise ValueError("message is required")

    chosen_model = model or XAI_MODEL
    if _local_first(message):
        return offline_reply(message)

    key = _api_key()
    if not _looks_like_xai_key(key):
        raise GrokClientError(
            "XAI_API_KEY is not an xAI key. Expected a key starting with xai- from https://console.x.ai"
        )

    brain = answer(message.strip())[:2800]
    payload = {
        "model": chosen_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Farnaz, the Warlock Grok local agent. "
                    "Never modify apps/local_agent or the original ChatGPT agent. "
                    "Use this brain when the user asks about DSP, Thall, oversample, ADAA, gate, or lab layout:\n"
                    + brain
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
