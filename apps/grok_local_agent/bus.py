import json
from datetime import datetime, timezone
from .config import STATE_DIR


def emit(kind: str, payload: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "events.jsonl"
    row = {"t": datetime.now(timezone.utc).isoformat(), "kind": kind, **payload}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
