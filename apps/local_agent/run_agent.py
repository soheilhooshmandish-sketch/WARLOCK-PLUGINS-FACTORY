import os
import winreg
import uvicorn


def load_token():
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        "Environment",
    )
    token, _ = winreg.QueryValueEx(
        key,
        "WARLOCK_AGENT_TOKEN",
    )

    if not token:
        raise RuntimeError("WARLOCK_AGENT_TOKEN is empty")

    os.environ["WARLOCK_AGENT_TOKEN"] = token


if __name__ == "__main__":
    load_token()

    uvicorn.run(
        "apps.local_agent.api:app",
        host="127.0.0.1",
        port=8765,
        log_level="info",
    )