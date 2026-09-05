"""4.5 desktop-lab tests. No paid API. Linux-safe."""
from __future__ import annotations

import math
import struct
import tempfile
import wave
from pathlib import Path

from apps.grok_local_agent.audio_lab import analyze
from apps.grok_local_agent.killswitch import guard, halt, halted, resume
from apps.grok_local_agent.profiles import match_title
from apps.grok_local_agent.tone import export_juce, propose
from apps.grok_local_agent.jobs import create, current, update
from apps.grok_local_agent.backup_gate import snapshot
from apps.grok_local_agent.config import AGENT_VERSION, PROTECTED_PATHS
from apps.grok_local_agent.plugin_val import inspect


def _wav(path: Path) -> None:
    sr = 48000
    n = sr // 2
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = b"".join(struct.pack("<h", int(12000 * math.sin(2 * math.pi * 110 * i / sr))) for i in range(n))
        wf.writeframes(frames)


def test_version():
    assert AGENT_VERSION.startswith("4.5")


def test_killswitch():
    resume()
    assert halted() is False
    halt("test")
    assert halted() is True
    assert guard()
    resume()
    assert halted() is False


def test_secret_still_blocked():
    from apps.grok_local_agent.operator import DENY_TYPE, grant, revoke, type_text
    resume()
    assert DENY_TYPE.search("api_key=sk-test")
    grant("type", 5, confirm=True)
    out = type_text("my api_key is secret")
    revoke("type")
    assert out.get("ok") is False
    assert "secret" in (out.get("error") or "").lower() or "POLICY" in (out.get("error") or "")



def test_profiles():
    assert "visual_studio" in match_title("Microsoft Visual Studio", "devenv")
    assert "fl_studio" in match_title("FL Studio 21", "FL64")


def test_audio_and_tone(tmp_path=None):
    d = Path(tempfile.mkdtemp())
    wav = d / "g.wav"
    _wav(wav)
    a = analyze(wav)
    assert a["ok"]
    assert "peak_db" in a
    prop = propose(str(wav), "THALL")
    assert prop["ok"]
    assert set(prop["tones"]) == {"A", "B", "C"}
    assert "GAIN" in prop["juce"]["A"]
    exp = export_juce(prop)
    assert exp["ok"] and exp["files"]


def test_jobs():
    job = create("Thall", "in progress")
    assert job["stage"] == "start"
    upd = update(job["id"], "analyze")
    assert upd["stage"] == "analyze"
    cur = current()
    assert any(j["id"] == job["id"] for j in cur["jobs"])


def test_backup_and_protect():
    snap = snapshot("test")
    assert snap["ok"]
    assert "apps/local_agent" in PROTECTED_PATHS


def test_plugin_val_honest():
    r = inspect()
    assert r["ok"]
    assert "pluginval" in r


if __name__ == "__main__":
    tests = [
        test_version, test_killswitch, test_secret_still_blocked, test_profiles,
        test_audio_and_tone, test_jobs, test_backup_and_protect, test_plugin_val_honest,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)
