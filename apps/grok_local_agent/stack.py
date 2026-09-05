"""Free/OSS stack status. Detect tools. Never fake a VST build."""
from __future__ import annotations

import shutil

from .config import AGENT_VERSION, PROJECT_ROOT

STACK = [
    ("Desktop Vision", "GDI screenshot; OpenCV optional", "wired"),
    ("Mouse / Keyboard", "Windows API; PyAutoGUI optional", "wired"),
    ("Audio analysis", "NumPy/SciPy; librosa optional", "local-fft"),
    ("DSP analysis", "preset brain + WARLOCK DSP cards", "wired"),
    ("JUCE / VST3", "JUCE + CMake", "detect"),
    ("A/B render", "FFmpeg", "detect"),
    ("Memory", "SQLite + JSON", "wired"),
    ("Backup", "Git", "wired"),
    ("Permission", "operator grants default-deny", "wired"),
    ("Build / test", "CMake + CTest + VS Build Tools", "detect"),
]


def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def report() -> str:
    tools = {
        "git": _has("git"),
        "cmake": _has("cmake"),
        "ctest": _has("ctest"),
        "ffmpeg": _has("ffmpeg"),
        "python": True,
        "numpy": False,
        "opencv": False,
        "juce_dir": (PROJECT_ROOT / "native").exists(),
    }
    try:
        import numpy  # noqa: F401
        tools["numpy"] = True
    except Exception:
        pass
    try:
        import cv2  # noqa: F401
        tools["opencv"] = True
    except Exception:
        pass
    lines = [
        f"Farnaz {AGENT_VERSION}  Free/OSS First",
        "Local Brain → free tools → DSP → JUCE → VST3",
        "Paid APIs are optional. WARLOCK_GROK_OFFLINE default on.",
        "",
    ]
    for name, tool, state in STACK:
        lines.append(f"{name:20} {state:10} {tool}")
    lines.append("")
    lines.append("detected: " + ", ".join(f"{k}={v}" for k, v in tools.items()))
    if not tools["cmake"]:
        lines.append("BUILD: cmake missing — will not claim a VST3 compile.")
    return "\n".join(lines)
