from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_NAME = "Farnaz"
AGENT_VERSION = "0.3.7"
AGENT_HOST = "127.0.0.1"
AGENT_PORT = 8766
STATIC_DIR = Path(__file__).resolve().parent / "static"

XAI_API_BASE = os.getenv("XAI_API_BASE", "https://api.x.ai/v1").rstrip("/")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4.6")


def offline_mode() -> bool:
    flag = (os.getenv("WARLOCK_GROK_OFFLINE") or "1").strip().lower()
    return flag in {"1", "true", "yes", "on"}
