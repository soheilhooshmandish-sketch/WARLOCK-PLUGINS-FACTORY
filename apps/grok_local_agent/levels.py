"""Five permission levels. Default deny. Does not bypass operator grants."""
from __future__ import annotations

from .operator import grant as grant_cap, require, status as op_status

LEVELS = {
    "read": ("see", "apps"),
    "safe": ("see", "apps", "launch"),
    "modify": ("see", "apps", "launch"),
    "build": ("see", "apps", "launch"),
    "system": ("see", "apps", "launch", "click", "type", "workflow"),
}

# Extra flags stored alongside grants
EXTRA = ("modify", "build")


def describe() -> dict:
    return {
        "levels": {
            "read": "Observe desktop and windows. No clicks.",
            "safe": "Open notepad/calc/explorer. Still no clicks.",
            "modify": "Change WARLOCK project files after backup. Never apps/local_agent.",
            "build": "Compile and read compiler output.",
            "system": "Mouse, keyboard, workflows. Kill switch can freeze this.",
        },
        "default": "deny",
        "operator": op_status(),
    }


def grant_level(level: str, minutes: int = 30, confirm: bool = False) -> dict:
    lv = (level or "").strip().lower()
    if lv not in LEVELS:
        return {"ok": False, "error": "unknown level", "levels": list(LEVELS)}
    if not confirm:
        return {"ok": False, "error": "confirm=true required"}
    import time
    from .operator import _load, _save

    granted = []
    for cap in LEVELS[lv]:
        grant_cap(cap, minutes, confirm=True)
        granted.append(cap)
    if lv in EXTRA:
        data = _load()
        data[lv] = {"until": time.time() + max(1, min(int(minutes), 120)) * 60, "at": time.time()}
        _save(data)
        granted.append(lv)
    return {"ok": True, "level": lv, "granted": granted, "minutes": minutes}



def need(level: str) -> str | None:
    from .killswitch import guard
    stop = guard()
    if stop:
        return stop
    lv = (level or "read").lower()
    if lv == "read":
        return require("see") or require("apps")
    if lv == "safe":
        return require("launch")
    if lv == "modify":
        from .operator import _load, _alive
        row = _load().get("modify") or {}
        if not _alive(float(row.get("until") or 0)):
            return "PERMISSION DENY: modify. Grant level MODIFY with confirm=true."
        return None
    if lv == "build":
        from .operator import _load, _alive
        row = _load().get("build") or {}
        if not _alive(float(row.get("until") or 0)):
            return "PERMISSION DENY: build. Grant level BUILD with confirm=true."
        return None
    if lv == "system":
        return require("click")
    return "PERMISSION DENY: unknown level"
