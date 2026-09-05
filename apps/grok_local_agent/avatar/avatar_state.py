"""Avatar mood. One state machine. No intelligence here."""
from __future__ import annotations

from enum import Enum
import threading
import time


class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    WORKING = "working"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


_lock = threading.RLock()
_state = State.IDLE
_detail = ""
_changed = 0.0
_hidden = False
_muted = False
_listeners: list = []

LABELS = {
    State.IDLE: {"en": "Ready", "fa": "آماده"},
    State.LISTENING: {"en": "Listening...", "fa": "گوش می‌دهد..."},
    State.THINKING: {"en": "Thinking...", "fa": "فکر می‌کند..."},
    State.SPEAKING: {"en": "Speaking...", "fa": "حرف می‌زند..."},
    State.WORKING: {"en": "Working...", "fa": "در حال کار..."},
    State.SUCCESS: {"en": "Done.", "fa": "انجام شد."},
    State.WARNING: {"en": "Permission needed", "fa": "مجوز لازم است"},
    State.ERROR: {"en": "Something failed", "fa": "خطا"},
}


def get_state() -> dict:
    with _lock:
        return {
            "state": _state.value,
            "detail": _detail,
            "changed": _changed,
            "hidden": _hidden,
            "muted": _muted,
            "label_en": LABELS[_state]["en"],
            "label_fa": LABELS[_state]["fa"],
        }


def set_state(state: State | str, detail: str = "") -> dict:
    global _state, _detail, _changed
    nxt = State(state) if not isinstance(state, State) else state
    with _lock:
        _state = nxt
        _detail = (detail or "")[:240]
        _changed = time.time()
        snap = get_state()
    for fn in list(_listeners):
        try:
            fn(snap)
        except Exception:
            pass
    return snap


def set_hidden(hidden: bool) -> dict:
    global _hidden
    with _lock:
        _hidden = bool(hidden)
    return get_state()


def set_muted(muted: bool) -> dict:
    global _muted
    with _lock:
        _muted = bool(muted)
    return get_state()


def subscribe(fn) -> None:
    _listeners.append(fn)
