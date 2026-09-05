"""Release gates. A script is not a pass."""
from __future__ import annotations

from pathlib import Path


def evaluate(vst3: Path | None, pluginval: dict | None, audio: dict | None, installer: Path | None, license_ok: bool) -> dict:
    exists = bool(vst3 and Path(vst3).exists())
    pv = bool(pluginval and pluginval.get("ok"))
    audio_pass = bool(audio and audio.get("ok") and audio.get("source") not in {None, "python-model"})
    inst = bool(installer and Path(installer).exists())
    gates = {
        "BUILD_PASS": exists,
        "PLUGINVAL_PASS": pv,
        "AUDIO_TEST_PASS": audio_pass,
        "REGRESSION_PASS": False,
        "LICENSE_PASS": license_ok,
        "PACKAGE_PASS": inst,
    }
    release = all(gates.values())
    return {
        "ok": release,
        "channel": "RELEASE" if release else "DEV",
        "gates": gates,
        "blocked": [k for k, v in gates.items() if not v],
    }
