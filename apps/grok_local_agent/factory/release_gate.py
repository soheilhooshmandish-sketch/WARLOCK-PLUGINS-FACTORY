"""Release is blocked unless every required gate is PASS. NOT_RUN blocks."""
from __future__ import annotations

from pathlib import Path

from ..killswitch import halted
from .licenses import dump as licenses

REQUIRED = (
    "PLUGINSPEC",
    "REALTIME_SAFETY",
    "BUILD",
    "PLUGIN_VALIDATION",
    "AUDIO_TEST",
    "GOLDEN_AUDIO",
    "NUMERICAL_SAFETY",
    "CPU",
    "LATENCY",
    "LICENSE",
    "PACKAGE",
)


def _st(value: str) -> str:
    return value if value in {"PASS", "WARNING", "FAIL", "NOT_RUN", "NOT_REQUIRED"} else "NOT_RUN"


def evaluate(results: dict | None = None) -> dict:
    results = results or {}
    if halted():
        return {
            "decision": "RELEASE_BLOCKED",
            "ok": False,
            "reason": "kill switch",
            "gates": {g: "FAIL" for g in REQUIRED},
        }
    gates = {g: _st(results.get(g, "NOT_RUN")) for g in REQUIRED}
    blocked = [g for g, st in gates.items() if st in {"FAIL", "NOT_RUN"}]
    warnings = [g for g, st in gates.items() if st == "WARNING"]
    lic = licenses()
    if lic.get("blocked"):
        gates["LICENSE"] = "FAIL"
        if "LICENSE" not in blocked:
            blocked.append("LICENSE")
    decision = "RELEASE_ALLOWED" if not blocked else "RELEASE_BLOCKED"
    return {
        "decision": decision,
        "ok": decision == "RELEASE_ALLOWED",
        "gates": gates,
        "blocked": blocked,
        "warnings": warnings,
        "note": "SOURCE≠BUILD≠VALIDATED≠TESTED≠RELEASE. Python golden is not AUDIO_TEST.",
    }


def from_artifacts(vst3: Path | None, pluginval: dict | None, audio: dict | None,
                   installer: Path | None, spec_status: str = "NOT_RUN",
                   rt_status: str = "NOT_RUN", golden_status: str = "NOT_RUN") -> dict:
    audio_pass = bool(audio and audio.get("ok") and audio.get("source") not in {None, "python-model"})
    return evaluate({
        "PLUGINSPEC": spec_status,
        "REALTIME_SAFETY": rt_status,
        "BUILD": "PASS" if vst3 and Path(vst3).exists() else "NOT_RUN",
        "PLUGIN_VALIDATION": "PASS" if pluginval and pluginval.get("ok") else "NOT_RUN",
        "AUDIO_TEST": "PASS" if audio_pass else "NOT_RUN",
        "GOLDEN_AUDIO": golden_status,
        "NUMERICAL_SAFETY": "NOT_RUN",
        "CPU": "NOT_RUN",
        "LATENCY": "NOT_RUN",
        "LICENSE": "PASS",
        "PACKAGE": "PASS" if installer and Path(installer).exists() else "NOT_RUN",
    })
