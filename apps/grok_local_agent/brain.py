from datetime import datetime, timezone
import json

from .aliases import normalize
from .config import AGENT_NAME, AGENT_VERSION, PELE_CAP, STATE_DIR
from .engine import run
from .facts import answer
from .progress import bump


def _mem(user: str, reply: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "memory.json"
    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append({"t": datetime.now(timezone.utc).isoformat(), "u": user[:400], "r": reply[:400]})
    path.write_text(json.dumps(data[-40:], ensure_ascii=False, indent=2), encoding="utf-8")


def reply(message: str) -> dict:
    text = normalize(message.strip())
    used, chunks = run(text)
    fact = answer(text)
    if fact:
        chunks = [fact] + chunks
        used = ["qa"] + used
    short = any(w in text.lower() for w in ("کوتاه", "short", "voice"))
    if short:
        chunks = [c[:280] for c in chunks[:2]]
    prog = bump(len(used))
    header = f"{AGENT_NAME} {AGENT_VERSION}  pele {prog.get('pele', 0)}/{PELE_CAP}"
    content = header + "\n\n" + "\n\n".join(chunks)
    try:
        _mem(text, content)
    except Exception:
        pass
    return {
        "model": "farnaz-v2.3-offline",
        "mode": "offline",
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "pele": prog.get("pele", 0),
        "pele_cap": PELE_CAP,
        "tools": used,
        "short": short,
        "content": content,
        "raw_id": "farnaz-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
    }
