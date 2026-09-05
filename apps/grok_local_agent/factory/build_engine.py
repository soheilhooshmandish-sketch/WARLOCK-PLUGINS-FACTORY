"""Controlled CMake/Clang build. Never SUCCESS without a real VST3 artifact."""
from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path

from ..killswitch import guard
from ..levels import need
from .toolchain import detect

CLANG_ERR = re.compile(r"(.+?):(\d+)(?::\d+)?: (error|warning): (.+)")
CMAKE_ERR = re.compile(r"CMake Error", re.I)
LINK_ERR = re.compile(r"(undefined reference|LNK\d+|ld:)", re.I)


def classify(log: str) -> str:
    if CMAKE_ERR.search(log) and "DPF" in log:
        return "FRAMEWORK ERROR"
    if CMAKE_ERR.search(log):
        return "CONFIGURATION ERROR"
    if LINK_ERR.search(log):
        return "LINKER ERROR"
    if "No such file" in log or "not found" in log.lower():
        return "MISSING RESOURCE"
    if CLANG_ERR.search(log):
        return "SOURCE ERROR"
    if "permission" in log.lower():
        return "DEPENDENCY ERROR"
    return "CONFIGURATION ERROR"


def build(source_dir: Path, build_dir: Path, max_repairs: int = 1) -> dict:
    stop = guard()
    if stop:
        return {"ok": False, "class": "DEPENDENCY ERROR", "error": stop}
    denied = need("build")
    if denied:
        return {"ok": False, "class": "DEPENDENCY ERROR", "error": denied, "state_hint": "WAITING_PERMISSION"}

    tools = detect()
    missing = tools["missing_required"]
    if "cmake" in missing or "dpf" in missing:
        return {
            "ok": False,
            "class": "CONFIGURATION ERROR",
            "error": "missing required tools: " + ", ".join(missing),
            "tools": tools["tools"],
            "vst3": None,
        }

    cmake = tools["tools"]["cmake"]["path"]
    build_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    cfg = subprocess.run(
        [cmake, "-S", str(source_dir), "-B", str(build_dir)],
        capture_output=True, text=True, timeout=120,
    )
    log = (cfg.stdout or "") + "\n" + (cfg.stderr or "")
    if cfg.returncode != 0:
        return {
            "ok": False,
            "class": classify(log),
            "exit": cfg.returncode,
            "duration": round(time.time() - started, 3),
            "log_tail": log[-4000:],
            "vst3": None,
            "max_repairs": max_repairs,
        }
    compiled = subprocess.run(
        [cmake, "--build", str(build_dir)],
        capture_output=True, text=True, timeout=300,
    )
    log2 = (compiled.stdout or "") + "\n" + (compiled.stderr or "")
    vst3 = _find_vst3(build_dir)
    ok = compiled.returncode == 0 and vst3 is not None
    return {
        "ok": ok,
        "class": None if ok else classify(log2),
        "exit": compiled.returncode,
        "duration": round(time.time() - started, 3),
        "log_tail": log2[-4000:],
        "vst3": str(vst3) if vst3 else None,
        "compiler": tools["tools"]["clang"]["path"] or tools["tools"]["g++"]["path"],
    }


def _find_vst3(root: Path) -> Path | None:
    hits = list(root.rglob("*.vst3"))
    for p in hits:
        if p.is_dir() or p.is_file():
            return p
    return None
