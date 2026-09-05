"""Emergency stop. Any automation checks this first."""
from __future__ import annotations

from pathlib import Path

from .config import STATE_DIR

FLAG = STATE_DIR / "EMERGENCY_STOP"


def halted() -> bool:
    return FLAG.exists()


def halt(reason: str = "user") -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    FLAG.write_text(reason[:200], encoding="utf-8")
    return {"ok": True, "stopped": True, "reason": reason}


def resume() -> dict:
    if FLAG.exists():
        FLAG.unlink()
    return {"ok": True, "stopped": False}


def guard() -> str | None:
    if halted():
        return "EMERGENCY STOP: all mouse/keyboard/build automation is frozen. Resume to continue."
    return None
