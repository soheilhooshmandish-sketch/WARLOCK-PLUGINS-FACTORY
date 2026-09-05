import json
from .config import STATE_DIR


def last(n: int = 3) -> str:
    path = STATE_DIR / "memory.json"
    if not path.exists():
        return "no memory yet"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "memory unreadable"
    rows = data[-n:]
    return "recall\n" + "\n".join(f"- {row.get('u', '')[:80]}" for row in rows)
