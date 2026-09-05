import json
from urllib.request import Request, urlopen

from .config import ORIGINAL_PORT


def probe(port: int, name: str) -> dict:
    url = f"http://127.0.0.1:{port}/health"
    try:
        req = Request(url, headers={"User-Agent": "FarnazOrchestrator/1"}, method="GET")
        with urlopen(req, timeout=0.8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"name": name, "port": port, "up": True, "agent": data.get("agent"), "version": data.get("version")}
    except Exception as exc:
        return {"name": name, "port": port, "up": False, "error": type(exc).__name__}


def fleet() -> str:
    rows = [
        probe(8766, "Farnaz"),
        probe(ORIGINAL_PORT, "Original ChatGPT (read-only)"),
        probe(8780, "Gateway"),
        probe(8790, "MCP"),
    ]
    lines = ["fleet (no writes to original)"]
    for row in rows:
        if row.get("up"):
            lines.append(f"UP   :{row['port']} {row['name']} {row.get('agent') or ''} {row.get('version') or ''}")
        else:
            lines.append(f"DOWN :{row['port']} {row['name']} {row.get('error')}")
    return "\n".join(lines)
