"""Detect local tools. Never install. Never download."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ..config import PROJECT_ROOT

Status = str  # AVAILABLE | MISSING | WRONG_VERSION | UNVERIFIED


def _which(name: str) -> str | None:
    return shutil.which(name)


def _ver(cmd: list[str]) -> str | None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
    except Exception:
        return None
    text = ((r.stdout or "") + " " + (r.stderr or "")).strip().splitlines()
    return (text[0] if text else "")[:120] or None


def _dir_ok(path: Path) -> bool:
    return path.exists() and path.is_dir()


def detect() -> dict:
    cmake = _which("cmake")
    clang = _which("clang++") or _which("clang")
    gxx = _which("g++")
    ninja = _which("ninja")
    cpack = _which("cpack")
    nsis = _which("makensis")
    pluginval = _which("pluginval")
    ffmpeg = _which("ffmpeg")
    git = _which("git")
    py = _which("python3") or _which("python")
    dpf_env = os.getenv("DPF_DIR")
    dpf_paths = [
        Path(dpf_env) if dpf_env else None,
        PROJECT_ROOT / "third_party" / "dpf",
        PROJECT_ROOT / "dpf",
    ]
    dpf = next((p for p in dpf_paths if p and _dir_ok(p)), None)
    iplug = PROJECT_ROOT / "third_party" / "iPlug2"
    juce = PROJECT_ROOT / "native"

    def st(found: bool) -> str:
        return "available" if found else "missing"

    tools = {
        "python": {"status": st(bool(py)), "path": py, "role": "REQUIRED"},
        "git": {"status": st(bool(git)), "path": git, "role": "REQUIRED"},
        "cmake": {"status": st(bool(cmake)), "path": cmake, "version": _ver(["cmake", "--version"]) if cmake else None, "role": "REQUIRED"},
        "clang": {"status": st(bool(clang)), "path": clang, "version": _ver(["clang++", "--version"]) if clang else None, "role": "REQUIRED"},
        "g++": {"status": st(bool(gxx)), "path": gxx, "role": "FALLBACK"},
        "ninja": {"status": st(bool(ninja)), "path": ninja, "role": "OPTIONAL"},
        "cpack": {"status": st(bool(cpack)), "path": cpack, "role": "REQUIRED"},
        "nsis": {"status": st(bool(nsis)), "path": nsis, "role": "REQUIRED"},
        "pluginval": {"status": st(bool(pluginval)), "path": pluginval, "role": "REQUIRED"},
        "ffmpeg": {"status": st(bool(ffmpeg)), "path": ffmpeg, "role": "OPTIONAL"},
        "dpf": {"status": st(bool(dpf)), "path": str(dpf) if dpf else None, "role": "REQUIRED"},
        "iplug2": {"status": st(_dir_ok(iplug)), "path": str(iplug) if _dir_ok(iplug) else None, "role": "FALLBACK"},
        "juce_legacy": {"status": st(_dir_ok(juce)), "path": str(juce) if _dir_ok(juce) else None, "role": "DEVELOPMENT-ONLY"},
    }
    missing = [k for k, v in tools.items() if v["status"] == "missing" and v["role"] == "REQUIRED"]
    return {
        "ok": True,
        "install_without_permission": False,
        "compiler_fallback": "g++" if gxx and not clang else None,
        "tools": tools,
        "missing_required": missing,
        "slice_ready": not missing,
        "note": "Farnaz will not download DPF, pluginval, CMake, LLVM, or NSIS. Ask first.",
    }


def summary() -> dict:
    d = detect()
    return {name: row["status"] for name, row in d["tools"].items()}
