"""Local tests for Farnaz avatar modules. No paid API."""
from __future__ import annotations

import json
from pathlib import Path

from apps.grok_local_agent.avatar.avatar_state import State, get_state, set_hidden, set_muted, set_state
from apps.grok_local_agent.avatar.lip_sync import detect_lang, duration_ms, visemes_from_text
from apps.grok_local_agent.avatar.speech_input import is_listening, start_ptt, stop_ptt
from apps.grok_local_agent.avatar.voice_engine import VoiceEngine
from apps.grok_local_agent.avatar.avatar_engine import identity
from apps.grok_local_agent.brain import answer
from apps.grok_local_agent.config import PROTECTED_PATHS


def test_state_machine():
    set_state(State.IDLE)
    assert get_state()["state"] == "idle"
    set_state(State.LISTENING)
    assert get_state()["state"] == "listening"
    set_state(State.THINKING)
    assert get_state()["state"] == "thinking"
    set_state(State.SPEAKING)
    assert get_state()["state"] == "speaking"
    set_state(State.WORKING, "Building WARLOCK THALL...")
    assert "THALL" in get_state()["detail"]
    set_state(State.SUCCESS)
    set_state(State.WARNING)
    set_state(State.ERROR)
    set_state(State.IDLE)
    assert get_state()["state"] == "idle"


def test_persian_visemes():
    frames = visemes_from_text("سلام فرناز")
    assert detect_lang("سلام فرناز") == "fa"
    assert frames[0]["mouth"]
    assert duration_ms(frames) > 0
    assert frames[-1]["mouth"] == "rest"


def test_english_visemes():
    frames = visemes_from_text("hello Farnaz")
    assert detect_lang("hello Farnaz") == "en"
    assert duration_ms(frames) > 0


def test_ptt_not_always_on():
    stop_ptt()
    assert is_listening() is False
    start_ptt("client")
    assert is_listening() is True
    stop_ptt()
    assert is_listening() is False


def test_voice_engine_no_crash():
    eng = VoiceEngine()
    out = eng.speak("ping")
    assert "visemes" in out
    assert out["spoken"] == "ping"
    eng.interrupt()


def test_identity_persistent():
    ident = identity()
    assert ident["name"] == "Farnaz"
    assert ident["identity_id"] == "farnaz-v1"


def test_brain_still_answers():
    text = answer("thall dsp gate")
    assert "Farnaz" in text or "THALL" in text or "dsp" in text.lower()


def test_chatgpt_agent_protected():
    assert "apps/local_agent" in PROTECTED_PATHS


def test_hidden_and_mute():
    set_hidden(True)
    assert get_state()["hidden"] is True
    set_hidden(False)
    set_muted(True)
    assert get_state()["muted"] is True
    set_muted(False)


if __name__ == "__main__":
    tests = [
        test_state_machine,
        test_persian_visemes,
        test_english_visemes,
        test_ptt_not_always_on,
        test_voice_engine_no_crash,
        test_identity_persistent,
        test_brain_still_answers,
        test_chatgpt_agent_protected,
        test_hidden_and_mute,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL", fn.__name__, exc)
    if failed:
        raise SystemExit(failed)
    print("OK", len(tests))
