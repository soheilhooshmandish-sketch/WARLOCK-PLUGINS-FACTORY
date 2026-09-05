"""Run pluginval as EXTERNAL process. Never link it into a WARLOCK binary."""
from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path


def parse(output: str, exit_code: int) -> dict:
    text = output or ""
    failed = exit_code != 0 or "FAILED" in text or "error" in text.lower() and "0 errors" not in text.lower()
    return {
        "ok": exit_code == 0 and not failed,
        "exit": exit_code,
        "failures": [ln.strip() for ln in text.splitlines() if "FAIL" in ln.upper()][:30],
        "warnings": [ln.strip() for ln in text.splitlines() if "warn" in ln.lower()][:30],
        "log_tail": text[-4000:],
    }


def run(vst3: str | Path, timeout: int = 180) -> dict:
    exe = shutil.which("pluginval")
    if not exe:
        return {
            "ok": False,
            "error": "pluginval missing",
            "status": "MISSING",
            "note": "EXTERNAL GPL-3 tool. Farnaz will not download it. Ask before install.",
        }
    path = Path(vst3)
    if not path.exists():
        return {"ok": False, "error": "vst3 artifact missing", "path": str(path)}
    started = time.time()
    r = subprocess.run(
        [exe, "--strictness-level", "5", "--validate", str(path)],
        capture_output=True, text=True, timeout=timeout,
    )
    report = parse((r.stdout or "") + "\n" + (r.stderr or ""), r.returncode)
    report["duration"] = round(time.time() - started, 3)
    report["path"] = str(path)
    return report
