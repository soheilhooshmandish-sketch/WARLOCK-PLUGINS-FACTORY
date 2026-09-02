from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_NAME = "Warlock Local Agent"
AGENT_VERSION = "0.2.0"

ALLOWED_OPERATIONS = {
    "python_version",
    "git_status",
    "git_branch",
}
