import os
from dataclasses import dataclass

import httpx


DEFAULT_AGENT_URL = "http://127.0.0.1:8765"


@dataclass(frozen=True)
class GatewayConfig:
    agent_url: str
    agent_token: str


def load_config() -> GatewayConfig:
    token = os.getenv("WARLOCK_AGENT_TOKEN")

    if not token:
        raise RuntimeError(
            "WARLOCK_AGENT_TOKEN is not configured"
        )

    agent_url = os.getenv(
        "WARLOCK_AGENT_URL",
        DEFAULT_AGENT_URL,
    ).rstrip("/")

    return GatewayConfig(
        agent_url=agent_url,
        agent_token=token,
    )


class WarlockGateway:
    def __init__(self, config: GatewayConfig):
        self.config = config

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": (
                f"Bearer {self.config.agent_token}"
            )
        }

    def health(self) -> dict:
        response = httpx.get(
            f"{self.config.agent_url}/health",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def git_status(self) -> dict:
        response = httpx.get(
            f"{self.config.agent_url}/git/status",
            headers=self._headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def read_file(self, path: str) -> dict:
        response = httpx.post(
            f"{self.config.agent_url}/files/read",
            headers=self._headers(),
            json={"path": path},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()


def create_gateway() -> WarlockGateway:
    return WarlockGateway(
        load_config()
    )
