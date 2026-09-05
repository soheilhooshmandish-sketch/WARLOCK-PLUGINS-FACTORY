from datetime import datetime
from pathlib import Path

from .config import AGENT_NAME, AGENT_VERSION, PROJECT_ROOT


def health_check():
    return {
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "status": "healthy",
        "workspace": str(PROJECT_ROOT),
        "cwd": str(Path.cwd()),
        "time": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    result = health_check()

    print("=" * 50)
    print(AGENT_NAME)
    print("=" * 50)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("=" * 50)
