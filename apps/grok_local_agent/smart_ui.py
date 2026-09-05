"""Click by name, not by coordinates. Observe → act → observe."""
from __future__ import annotations

from .actions import record
from .killswitch import guard
from .operator import click, require
from .vision import find_control, scene

MIN_CONF = 0.7


def _summary(sc: dict) -> dict:
    if not sc:
        return {}
    return {
        "apps": [a.get("app") for a in (sc.get("apps_detected") or [])][:6],
        "controls": len(sc.get("controls") or []),
        "titles": [w.get("title") for w in (sc.get("windows") or [])][:4],
    }


def click_named(name: str) -> dict:
    stop = guard()
    if stop:
        return {"ok": False, "error": stop}
    err = require("click") or require("see")
    if err:
        return {"ok": False, "error": err}
    before = scene() if not require("see") else {}
    ctrl = find_control(name)
    if not ctrl:
        record("click_named", f"miss:{name}", False)
        return {
            "ok": False,
            "error": f'control not found: "{name}"',
            "hint": "Grant SEE + CLICK. Visual Studio exposes Build. FL Studio often has no UIA names.",
            "apps_detected": (before or {}).get("apps_detected"),
            "before": _summary(before),
        }
    conf = float(ctrl.get("confidence") or 0)
    if conf < MIN_CONF:
        record("click_named", f"low-conf:{name}:{conf}", False)
        return {
            "ok": False,
            "error": "low confidence — will not click blindly",
            "confidence": conf,
            "control": ctrl,
        }
    result = click(int(ctrl["x"]), int(ctrl["y"]), "left")
    after = scene() if result.get("ok") and not require("see") else {}
    result["named"] = name
    result["control"] = ctrl
    result["confidence"] = conf
    result["before"] = _summary(before)
    result["after"] = _summary(after)
    result["loop"] = "observe-act-verify"
    record("click_named", f"{name} conf={conf:.2f}", bool(result.get("ok")))
    return result
