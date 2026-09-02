from __future__ import annotations

import importlib


CRITICAL_MODULES = (
    "fastapi",
    "uvicorn",
    "httpx",
    "jwt",
    "cryptography",
    "mcp",
    "apps.runtime_supervisor",
    "apps.local_agent.api",
    "apps.gateway.server",
    "apps.mcp_server.server",
)


def main() -> int:
    for module_name in CRITICAL_MODULES:
        importlib.import_module(module_name)

    from apps.gateway.server import app as gateway_app
    from apps.local_agent.api import app as agent_app
    from apps.mcp_server.server import app as mcp_app

    if agent_app is None or gateway_app is None or mcp_app is None:
        raise RuntimeError("One or more Warlock ASGI applications failed to initialize")

    print("Warlock runtime preflight: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
