"""Desktop Operator for Farnaz. Default-deny. Loopback only. Never touches apps/local_agent."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from .config import STATE_DIR
from .killswitch import guard, halt
from .windows import _ps, screenshot, start_app, APPS

CAPS = ("see", "apps", "click", "type", "launch", "workflow")
STORE = STATE_DIR / "operator_grants.json"
MAX_TYPE = 200
MAX_STEPS = 8
SAFE_TYPE = re.compile(r"^[\w\s.,;:!?'\"#@/+\-\[\]()]*$", re.UNICODE)
DENY_TYPE = re.compile(r"(password|passwd|api[_-]?key|secret|token|ssh-rsa)", re.I)


def _load() -> dict:
    if not STORE.exists():
        return {}
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _alive(until: float) -> bool:
    return until > time.time()


def status() -> dict:
    data = _load()
    now = time.time()
    grants = {}
    for cap in CAPS:
        row = data.get(cap) or {}
        until = float(row.get("until") or 0)
        grants[cap] = {
            "allowed": _alive(until),
            "until": int(until) if _alive(until) else None,
            "minutes_left": max(0, int((until - now) / 60)) if _alive(until) else 0,
        }
    return {
        "role": "desktop-operator",
        "host": "127.0.0.1",
        "windows": os.name == "nt",
        "default": "deny",
        "grants": grants,
        "allowed_apps": sorted(set(APPS.values())),
        "rule": "Farnaz never controls apps/local_agent. Screenshot stays on this machine.",
    }


def grant(capability: str, minutes: int = 30, confirm: bool = False) -> dict:
    cap = capability.strip().lower()
    if cap not in CAPS:
        return {"ok": False, "error": "unknown capability", "caps": list(CAPS)}
    if not confirm:
        return {"ok": False, "error": "confirm=true required to grant " + cap}
    minutes = max(1, min(int(minutes or 30), 120))
    data = _load()
    data[cap] = {"until": time.time() + minutes * 60, "at": time.time()}
    _save(data)
    return {"ok": True, "granted": cap, "minutes": minutes}


def revoke(capability: str | None = None) -> dict:
    data = _load()
    if capability:
        cap = capability.strip().lower()
        data.pop(cap, None)
        _save(data)
        return {"ok": True, "revoked": cap}
    _save({})
    return {"ok": True, "revoked": "all"}


def require(cap: str) -> str | None:
    row = _load().get(cap) or {}
    if not _alive(float(row.get("until") or 0)):
        return f"PERMISSION DENY: {cap}. Grant with confirm=true first."
    return None


def see() -> dict:
    err = require("see")
    if err:
        return {"ok": False, "error": err}
    note = screenshot()
    path = STATE_DIR / "screenshot.png"
    return {
        "ok": True,
        "op": "see",
        "note": note,
        "path": str(path) if path.exists() else None,
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def apps() -> dict:
    err = require("apps")
    if err:
        return {"ok": False, "error": err}
    raw = _ps(
        "Get-Process | Where-Object { $_.MainWindowTitle } | "
        "Select-Object -First 40 Name,Id,MainWindowTitle | "
        "ConvertTo-Csv -NoTypeInformation"
    )
    rows = []
    for line in raw.splitlines()[1:]:
        parts = [p.strip().strip('"') for p in line.split(",", 2)]
        if len(parts) >= 3 and parts[2]:
            rows.append({"name": parts[0], "id": parts[1], "title": parts[2][:80]})
    return {"ok": True, "op": "apps", "windows": rows, "count": len(rows)}


def click(x: int, y: int, button: str = "left") -> dict:
    stop = guard()
    if stop:
        return {"ok": False, "error": stop}
    err = require("click")
    if err:
        return {"ok": False, "error": err}
    if os.name != "nt":
        return {"ok": False, "error": "windows-only"}
    x, y = int(x), int(y)
    if not (0 <= x <= 10000 and 0 <= y <= 10000):
        return {"ok": False, "error": "coords out of range"}
    btn = (button or "left").lower()
    down, up = (2, 4) if btn != "right" else (8, 16)
    note = _ps(
        "Add-Type -TypeDefinition @\"\n"
        "using System; using System.Runtime.InteropServices;\n"
        "public static class FIn {\n"
        "  [DllImport(\"user32.dll\")] public static extern bool SetCursorPos(int X, int Y);\n"
        "  [DllImport(\"user32.dll\")] public static extern void mouse_event(uint f, int a, int b, uint d, UIntPtr e);\n"
        "}\n\"@\n"
        f"[FIn]::SetCursorPos({x},{y}); "
        f"[FIn]::mouse_event({down},0,0,0,[UIntPtr]::Zero); "
        f"[FIn]::mouse_event({up},0,0,0,[UIntPtr]::Zero); "
        f"'clicked {btn} {x},{y}'"
    )
    return {"ok": True, "op": "click", "x": x, "y": y, "button": btn, "note": note}


def type_text(text: str) -> dict:
    stop = guard()
    if stop:
        return {"ok": False, "error": stop}
    err = require("type")
    if err:
        return {"ok": False, "error": err}
    payload = (text or "")[:MAX_TYPE]
    if not payload.strip():
        return {"ok": False, "error": "empty"}
    if DENY_TYPE.search(payload):
        return {"ok": False, "error": "POLICY DENY: looks like a secret"}
    if not SAFE_TYPE.match(payload):
        return {"ok": False, "error": "POLICY DENY: unsafe characters"}
    os.environ["FARNAZ_TYPE"] = payload
    note = _ps(
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[Windows.Forms.SendKeys]::SendWait($env:FARNAZ_TYPE); 'typed'"
    )
    return {"ok": True, "op": "type", "chars": len(payload), "note": note}


def launch(app: str) -> dict:
    err = require("launch")
    if err:
        return {"ok": False, "error": err}
    name = (app or "").strip().lower()
    if "local_agent" in name or "python" == name:
        return {"ok": False, "error": "POLICY DENY: protected process"}
    return {"ok": True, "op": "launch", "note": start_app(name)}


def run_step(step: dict) -> dict:
    op = str(step.get("op") or "").lower()
    if op == "see":
        return see()
    if op == "apps":
        return apps()
    if op == "click":
        return click(step.get("x") or 0, step.get("y") or 0, step.get("button") or "left")
    if op == "type":
        return type_text(str(step.get("text") or ""))
    if op == "launch":
        return launch(str(step.get("app") or ""))
    if op == "wait":
        ms = max(0, min(int(step.get("ms") or 400), 4000))
        time.sleep(ms / 1000)
        return {"ok": True, "op": "wait", "ms": ms}
    return {"ok": False, "error": "unknown op " + op}


def workflow(steps: list) -> dict:
    stop = guard()
    if stop:
        return {"ok": False, "error": stop}
    err = require("workflow")
    if err:
        return {"ok": False, "error": err}
    if not isinstance(steps, list) or not steps:
        return {"ok": False, "error": "steps required"}
    if len(steps) > MAX_STEPS:
        return {"ok": False, "error": f"max {MAX_STEPS} steps"}
    log = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            return {"ok": False, "error": f"step {i} not an object", "log": log}
        result = run_step(step)
        log.append(result)
        if not result.get("ok"):
            return {"ok": False, "stopped": i, "log": log}
    return {"ok": True, "op": "workflow", "steps": len(log), "log": log}


def route(text: str) -> str:
    key = text.lower()
    if any(w in key for w in ("emergency", "kill switch", "توقف اضطراری", "بایست فوری")):
        return json.dumps(halt("chat"), ensure_ascii=False)
    if any(w in key for w in ("روی ", "click ", "کلیک")):
        from .smart_ui import click_named
        name = text
        for prefix in ("روی ", "click ", "کلیک کن روی ", "کلیک "):
            if prefix in key:
                name = text.split(prefix, 1)[-1].strip(" .")
                break
        return json.dumps(click_named(name), ensure_ascii=False)
    if any(w in key for w in ("ببین صفحه", "vision", "چه چیزی روی", "scene")):
        from .vision import scene
        return json.dumps(scene(), ensure_ascii=False)
    if any(w in key for w in ("revoke all", "پس بگیر همه", "لغو همه")):
        return json.dumps(revoke(), ensure_ascii=False)
    m = re.search(r"(grant|مجوز)\s+(\w+)", key)
    if m:
        return json.dumps(grant(m.group(2), 30, confirm=True), ensure_ascii=False)
    if any(w in key for w in ("operator", "اپراتور", "مجوز", "permission", "desktop operator")):
        return json.dumps(status(), ensure_ascii=False, indent=2)
    if any(w in key for w in ("ببین", "see desktop", "vision", "اسکرین", "screenshot")):
        return json.dumps(see(), ensure_ascii=False)
    if any(w in key for w in ("برنامه", "apps", "windows list", "پنجره")):
        return json.dumps(apps(), ensure_ascii=False)
    return json.dumps(status(), ensure_ascii=False, indent=2)
