"""Compat wrapper around release_gate."""
from pathlib import Path

from .release_gate import evaluate as _eval
from .release_gate import from_artifacts


def evaluate(vst3: Path | None, pluginval: dict | None, audio: dict | None, installer: Path | None, license_ok: bool) -> dict:
    g = from_artifacts(vst3, pluginval, audio, installer)
    return {
        "ok": g["ok"],
        "channel": "RELEASE" if g["ok"] else "DEV",
        "gates": {
            "BUILD_PASS": g["gates"]["BUILD"] == "PASS",
            "PLUGINVAL_PASS": g["gates"]["PLUGIN_VALIDATION"] == "PASS",
            "AUDIO_TEST_PASS": g["gates"]["AUDIO_TEST"] == "PASS",
            "REGRESSION_PASS": g["gates"]["GOLDEN_AUDIO"] == "PASS",
            "LICENSE_PASS": license_ok and g["gates"]["LICENSE"] != "FAIL",
            "PACKAGE_PASS": g["gates"]["PACKAGE"] == "PASS",
        },
        "blocked": g["blocked"],
        "decision": g["decision"],
    }
