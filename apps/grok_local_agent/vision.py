"""On-demand desktop scene. UI Automation + window titles + screenshot. No paid vision API."""
from __future__ import annotations

import json
import os
import shutil

from .config import STATE_DIR
from .killswitch import guard
from .operator import apps, require, see as snap
from .profiles import PROFILES, match_title
from .windows import _ps


UIA_LIST = r"""
Add-Type -AssemblyName UIAutomationClient
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Button)
$btns = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $cond)
$n = 0
$rows = @()
foreach ($b in $btns) {
  if ($n -ge 60) { break }
  $name = $b.Current.Name
  if (-not $name) { continue }
  $r = $b.Current.BoundingRectangle
  if ($r.Width -lt 2 -or $r.Height -lt 2) { continue }
  $rows += [pscustomobject]@{
    name = $name.Substring(0, [Math]::Min(80, $name.Length))
    type = 'Button'
    x = [int]($r.X + $r.Width/2)
    y = [int]($r.Y + $r.Height/2)
    w = [int]$r.Width
    h = [int]$r.Height
  }
  $n++
}
if ($rows.Count -eq 0) { '[]' } else { $rows | ConvertTo-Json -Compress }
"""


def _controls() -> list[dict]:
    if os.name != "nt":
        return []
    raw = _ps(UIA_LIST, timeout=12)
    raw = raw.strip()
    if not raw.startswith("[") and not raw.startswith("{"):
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if isinstance(data, dict):
        return [data]
    return [c for c in data if isinstance(c, dict)][:60]


def _ocr_note() -> str | None:
    if shutil.which("tesseract"):
        return "tesseract present — optional OCR not run unless requested"
    return None


def scene() -> dict:
    stop = guard()
    if stop:
        return {"ok": False, "error": stop}
    err = require("see")
    if err:
        return {"ok": False, "error": err}
    shot = snap()
    windows = apps() if not require("apps") else {"windows": []}
    wins = windows.get("windows") or []
    controls = _controls()
    matches = []
    for w in wins:
        hits = match_title(w.get("title") or "", w.get("name") or "")
        if hits:
            matches.append({"window": w, "profiles": hits})
    findings = []
    for m in matches:
        for name in m["profiles"]:
            prof = PROFILES[name]
            names = {c.get("name", "").lower() for c in controls}
            found = [k for k in prof.get("look_for", []) if k.lower() in " ".join(names) or k.lower() in (m["window"].get("title") or "").lower()]
            fail = [h for h in prof.get("fail_hints", []) if h.lower() in (m["window"].get("title") or "").lower()]
            findings.append({
                "app": name,
                "title": m["window"].get("title"),
                "look_hits": found,
                "fail_hits": fail,
                "note": prof.get("note"),
            })
    return {
        "ok": True,
        "op": "vision",
        "backend": "uia+titles+screenshot",
        "paid_api": False,
        "screenshot": shot,
        "windows": wins[:20],
        "controls": controls,
        "apps_detected": findings,
        "ocr": _ocr_note(),
        "cpu": "on-demand only",
    }


def find_control(name: str) -> dict | None:
    want = (name or "").strip().lower()
    if not want:
        return None
    for c in _controls():
        label = str(c.get("name") or "").lower()
        if want in label or label in want:
            return c
    for prof in PROFILES.values():
        alias = (prof.get("click") or {}).get(want)
        if alias:
            return find_control(alias)
    return None
