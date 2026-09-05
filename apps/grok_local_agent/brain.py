from datetime import datetime, timezone
import json

from .bus import emit
from .config import AGENT_NAME, AGENT_VERSION, PELE_CAP, STATE_DIR
from .critic import review
from .engine import run
from .facts import answer
from .perceive import perceive
from .policy import guard_path, is_locked
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
    p = perceive(message)
    used: list[str] = ["perceive"]
    chunks: list[str] = []

    if p.path and is_locked(p.path):
        deny = guard_path(p.path)
        used.append("policy-deny")
        chunks.append(deny or "denied")
        emit("deny", {"path": p.path})
    elif p.wants_write and p.path and is_locked(p.path):
        used.append("policy-deny-write")
        chunks.append("POLICY DENY write on original agent")
    else:
        fact = answer(p.text)
        if fact:
            used.append("qa")
            chunks.append(fact)
        tool_used, tool_chunks = run(p.text)
        used.extend(tool_used)
        chunks.extend(tool_chunks)

    prog = bump(len(used))
    header = f"{AGENT_NAME} {AGENT_VERSION}  pele {prog.get('pele', 0)}/{PELE_CAP}"
    body = review(chunks, p.short)
    content = header + "\n\n" + body
    try:
        _mem(p.text, content)
        emit("reply", {"tools": used, "short": p.short, "pele": prog.get("pele", 0)})
    except Exception:
        pass
    return {
        "model": "farnaz-v3-arch",
        "mode": "offline",
        "agent": AGENT_NAME,
        "version": AGENT_VERSION,
        "pele": prog.get("pele", 0),
        "pele_cap": PELE_CAP,
        "tools": used,
        "short": p.short,
        "content": content,
        "raw_id": "farnaz-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
    }
