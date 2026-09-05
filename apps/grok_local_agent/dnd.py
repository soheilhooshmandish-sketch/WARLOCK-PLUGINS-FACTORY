"""Do Not Disturb while recording / performing. Pause speech and heavy vision."""
from __future__ import annotations

from .config import STATE_DIR

FLAG = STATE_DIR / "DND"


def on() -> bool:
    return FLAG.exists()


def enable(reason: str = "recording") -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    FLAG.write_text(reason[:80], encoding="utf-8")
    return {"ok": True, "dnd": True, "reason": reason}


def disable() -> dict:
    if FLAG.exists():
        FLAG.unlink()
    return {"ok": True, "dnd": False}


def block_speech() -> str | None:
    if on():
        return "DND: recording/session. Speech and heavy vision paused."
    return None
