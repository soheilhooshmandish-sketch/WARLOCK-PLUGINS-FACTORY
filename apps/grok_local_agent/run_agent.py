import os
import winreg

import uvicorn

from .config import AGENT_HOST, AGENT_PORT


def load_user_env(*names: str) -> None:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
    for name in names:
        try:
            value, _ = winreg.QueryValueEx(key, name)
        except FileNotFoundError:
            continue
        if value:
            os.environ[name] = str(value)


def load_token():
    load_user_env(
        "WARLOCK_GROK_AGENT_TOKEN",
        "WARLOCK_AGENT_TOKEN",
        "XAI_API_KEY",
        "GROK_API_KEY",
    )
    if os.getenv("XAI_API_KEY") and not os.getenv("GROK_API_KEY"):
        os.environ["GROK_API_KEY"] = os.environ["XAI_API_KEY"]
    if os.getenv("GROK_API_KEY") and not os.getenv("XAI_API_KEY"):
        os.environ["XAI_API_KEY"] = os.environ["GROK_API_KEY"]

    if not os.getenv("WARLOCK_GROK_AGENT_TOKEN") and not os.getenv("WARLOCK_AGENT_TOKEN"):
        raise RuntimeError("No agent token is configured")

    if os.getenv("XAI_API_KEY"):
        print("XAI_API_KEY: present")
    else:
        print("XAI_API_KEY: missing")


if __name__ == "__main__":
    load_token()
    uvicorn.run(
        "apps.grok_local_agent.api:app",
        host=AGENT_HOST,
        port=AGENT_PORT,
        log_level="info",
    )
