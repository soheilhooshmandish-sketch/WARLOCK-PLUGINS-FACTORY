from pathlib import Path
from datetime import datetime


AGENT_NAME = "Warlock Local Agent"
AGENT_VERSION = "0.1.0"


def health_check():
    return {
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "status": "healthy",
        "workspace": str(Path.cwd()),
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
