"""Click by name, not by coordinates. Uses vision controls + existing click()."""
from __future__ import annotations

from .killswitch import guard
from .operator import click, require
from .vision import find_control, scene


def click_named(name: str) -> dict:
    stop = guard()
    if stop:
        return {"ok": False, "error": stop}
    err = require("click") or require("see")
    if err:
        return {"ok": False, "error": err}
    ctrl = find_control(name)
    if not ctrl:
        # refresh scene so the user sees why
        sc = scene() if not require("see") else {}
        return {
            "ok": False,
            "error": f'control not found: "{name}"',
            "hint": "Grant SEE + CLICK. Visual Studio exposes Build. FL Studio often has no UIA names.",
            "apps_detected": (sc or {}).get("apps_detected"),
        }
    result = click(int(ctrl["x"]), int(ctrl["y"]), "left")
    result["named"] = name
    result["control"] = ctrl
    return result
