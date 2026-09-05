"""Build / debug. Never writes source without MODIFY. Never touches apps/local_agent."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from .backup_gate import snapshot
from .config import PROJECT_ROOT, PROTECTED_PATHS
from .killswitch import guard
from .levels import need

ERR = re.compile(r"(.+?)\((\d+)(?:,\d+)?\):\s+(error|warning)\s+(\w+):\s+(.+)", re.I)


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> dict:
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    text = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
    issues = []
    for m in ERR.finditer(text):
        rel = m.group(1).replace("\\", "/")
        if any(rel.endswith(p) or f"/{p}/" in rel for p in PROTECTED_PATHS):
            continue
        issues.append({"file": rel, "line": int(m.group(2)), "kind": m.group(3).lower(), "code": m.group(4), "msg": m.group(5)[:200]})
    return {
        "ok": r.returncode == 0,
        "exit": r.returncode,
        "log_tail": text[-3000:],
        "issues": issues[:20],
    }


def build(target: str = "native/warlock_thall") -> dict:
    stop = guard()
    if stop:
        return {"ok": False, "error": stop}
    denied = need("build")
    if denied:
        return {"ok": False, "error": denied}
    snap = snapshot("pre-build")
    root = PROJECT_ROOT / target
    if not root.exists():
        return {"ok": False, "error": f"missing {target}", "backup": snap}
    if not shutil.which("cmake"):
        return {
            "ok": False,
            "error": "cmake missing — will not claim a VST3 compile",
            "backup": snap,
            "next": "Install CMake + VS Build Tools, then grant BUILD.",
        }
    build_dir = root / "build"
    cfg = _run(["cmake", "-S", str(root), "-B", str(build_dir)], PROJECT_ROOT)
    if not cfg.get("ok"):
        return {"ok": False, "stage": "configure", "backup": snap, **cfg}
    compiled = _run(["cmake", "--build", str(build_dir), "--config", "Release"], PROJECT_ROOT, timeout=300)
    return {"ok": compiled.get("ok"), "stage": "build", "backup": snap, "configure": cfg, "build": compiled}


def suggest_fix(issues: list[dict]) -> list[dict]:
    out = []
    for it in issues:
        msg = (it.get("msg") or "").lower()
        hint = "Read the file at that line. Do not auto-edit without MODIFY."
        if "undeclared" in msg or "not declared" in msg:
            hint = "Missing include or typo in identifier."
        elif "lnk" in (it.get("code") or "").lower():
            hint = "Linker: library or object not in CMakeLists."
        out.append({**it, "hint": hint, "auto_edit": False})
    return out
