from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_NAME = "Warlock Local Agent"
AGENT_VERSION = "0.3.0"
AGENT_HOST = "127.0.0.1"
AGENT_PORT = 8765

ALLOWED_OPERATIONS = {
    "python_version",
    "git_status",
    "git_branch",
}

XAI_API_BASE = os.getenv("XAI_API_BASE", "https://api.x.ai/v1").rstrip("/")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4")
