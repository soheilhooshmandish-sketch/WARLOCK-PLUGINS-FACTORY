import os
import winreg

import uvicorn

from .config import AGENT_HOST, AGENT_PORT


def load_token():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
    for name in ("WARLOCK_GROK_AGENT_TOKEN", "WARLOCK_AGENT_TOKEN"):
        try:
            token, _ = winreg.QueryValueEx(key, name)
        except FileNotFoundError:
            continue
        if token:
            os.environ[name] = token
            if name == "WARLOCK_GROK_AGENT_TOKEN":
                break
            if not os.getenv("WARLOCK_GROK_AGENT_TOKEN"):
                os.environ["WARLOCK_GROK_AGENT_TOKEN"] = token

    if not os.getenv("WARLOCK_GROK_AGENT_TOKEN") and not os.getenv("WARLOCK_AGENT_TOKEN"):
        raise RuntimeError("No agent token is configured")


if __name__ == "__main__":
    load_token()
    uvicorn.run(
        "apps.grok_local_agent.api:app",
        host=AGENT_HOST,
        port=AGENT_PORT,
        log_level="info",
    )
