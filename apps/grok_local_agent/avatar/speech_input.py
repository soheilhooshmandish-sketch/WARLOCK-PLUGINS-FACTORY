"""Push-to-talk only. Mic is never always-on."""
from __future__ import annotations

import threading
import time

from .avatar_state import State, set_state

_lock = threading.Lock()
_listening = False
_started = 0.0
_backend = "none"


def is_listening() -> bool:
    with _lock:
        return _listening


def status() -> dict:
    with _lock:
        return {
            "listening": _listening,
            "backend": _backend,
            "started": _started,
            "always_on": False,
            "note": "Hold PTT. Mic stops on release. Audio stays on this machine unless you later opt into an online STT.",
        }


def start_ptt(backend: str = "client") -> dict:
    global _listening, _started, _backend
    with _lock:
        _listening = True
        _started = time.time()
        _backend = backend if backend in {"client", "vosk", "sapi"} else "client"
    set_state(State.LISTENING, "push-to-talk")
    return status()


def stop_ptt() -> dict:
    global _listening
    with _lock:
        was = _listening
        _listening = False
    if was:
        set_state(State.IDLE, "mic closed")
    return status()
