import json
from pathlib import Path

from .config import PELE_CAP, STATE_DIR


def bump(steps: int) -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "pele.json"
    data = {"pele": 0, "sessions": 0}
    if path.exists():
        try:
            data.update(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            pass
    data["pele"] = min(PELE_CAP, int(data.get("pele", 0)) + max(1, steps))
    data["sessions"] = int(data.get("sessions", 0)) + 1
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def read() -> dict:
    path = STATE_DIR / "pele.json"
    if not path.exists():
        return {"pele": 0, "sessions": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"pele": 0, "sessions": 0}
