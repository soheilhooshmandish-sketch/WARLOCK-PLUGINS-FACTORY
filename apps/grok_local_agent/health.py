"""Lightweight startup health. No expensive tests."""
from __future__ import annotations

import os
import shutil

from .avatar.speech_input import is_listening
from .avatar.voice_engine import VoiceEngine
from .config import AGENT_VERSION, PROJECT_ROOT
from .killswitch import halted


def report() -> dict:
    git = shutil.which("git") is not None
    cmake = shutil.which("cmake") is not None
    juce = (PROJECT_ROOT / "native").exists()
    return {
        "version": AGENT_VERSION,
        "brain": "ok",
        "desktop": "ok" if os.name == "nt" else "degraded-not-windows",
        "vision": "ok" if os.name == "nt" else "degraded-not-windows",
        "microphone": "idle" if not is_listening() else "listening",
        "voice": ",".join(VoiceEngine().list_backends()),
        "git": "ok" if git else "missing",
        "audio": "ok",
        "juce": "ok" if juce else "missing-native",
        "compiler": "ok" if cmake else "missing-cmake",
        "halted": halted(),
        "paid_api_required": False,
    }
