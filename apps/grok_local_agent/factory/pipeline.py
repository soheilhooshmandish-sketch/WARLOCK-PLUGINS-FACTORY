"""Minimal vertical slice. Stops honestly when tools are missing. Not THALL."""
from __future__ import annotations

from pathlib import Path

from ..avatar.avatar_state import State, set_state
from ..backup_gate import snapshot
from ..config import PROJECT_ROOT, STATE_DIR
from ..dnd import on as dnd_on
from . import factory_jobs as FJ
from .adapter import generate
from .bench import run as bench
from .build_engine import build
from .packager import prepare
from .pluginval_parse import run as pluginval
from .spec import probe_spec
from .toolchain import detect


def slice_probe(starting_sha: str, backup_ref: str) -> dict:
    try:
        from ..dnd import on as dnd_on
        if dnd_on():
            return {"ok": False, "error": "DND on — defer heavy factory work"}
    except Exception:
        pass
    tools = detect()
    spec = probe_spec()
    snap = snapshot("factory-probe")
    job = FJ.create(
        spec.plugin,
        spec.plugin_type,
        spec.framework,
        starting_git_sha=starting_sha,
        backup_ref=backup_ref,
        dsp_spec=spec.to_dict(),
        parameters=[p.__dict__ for p in spec.parameters],
        target_description="factory proof — not THALL",
    )
    FJ.set_state(job["job_id"], "GENERATING")
    gen = generate(spec)
    if not gen.get("ok"):
        FJ.set_state(job["job_id"], "FAILED", errors=str(gen))
        set_state(State.ERROR, "generate failed")
        return {"ok": False, "job": job["job_id"], "generate": gen, "tools": tools}

    missing = tools["missing_required"]
    if missing:
        FJ.set_state(
            job["job_id"],
            "WAITING_PERMISSION",
            errors="missing: " + ", ".join(missing),
            build_directory=gen.get("dir"),
        )
        set_state(State.WARNING, "tools missing")
        pack = prepare(STATE_DIR / "factory" / "WARLOCK-Probe", None)
        return {
            "ok": False,
            "milestone": False,
            "reason": "required tools missing; will not download",
            "missing_required": missing,
            "job": job["job_id"],
            "spec": spec.to_dict(),
            "generate": gen,
            "tools": {k: v["status"] for k, v in tools["tools"].items()},
            "packager_scripts": pack,
            "vst3": None,
            "pluginval": None,
            "installer": None,
        }

    FJ.set_state(job["job_id"], "BUILDING")
    built = build(Path(gen["dir"]), Path(gen["dir"]) / "build")
    if not built.get("ok"):
        FJ.set_state(job["job_id"], "BUILD_FAILED", errors=built.get("error") or built.get("class"))
        set_state(State.ERROR, "build failed")
        return {"ok": False, "milestone": False, "job": job["job_id"], "build": built}

    FJ.set_state(job["job_id"], "VALIDATING", output_vst3=built.get("vst3"))
    val = pluginval(built["vst3"])
    if not val.get("ok"):
        FJ.set_state(job["job_id"], "VALIDATION_FAILED", validation_result=val)
        return {"ok": False, "milestone": False, "job": job["job_id"], "build": built, "pluginval": val}

    tests = bench(Path(built["vst3"]))
    FJ.set_state(job["job_id"], "PACKAGING", test_result=tests)
    pack = prepare(PROJECT_ROOT / "output" / "WARLOCK-Probe", Path(built["vst3"]))
    if not pack.get("installer"):
        FJ.set_state(job["job_id"], "FAILED", installer_path=None, errors=pack.get("error"))
        return {"ok": False, "milestone": False, "job": job["job_id"], "build": built, "pluginval": val, "tests": tests, "package": pack}

    FJ.set_state(job["job_id"], "DONE", installer_path=pack.get("installer"), final_sha=starting_sha)
    set_state(State.SUCCESS, "factory slice done")
    return {
        "ok": True,
        "milestone": True,
        "job": job["job_id"],
        "vst3": built.get("vst3"),
        "pluginval": val,
        "tests": tests,
        "installer": pack.get("installer"),
    }
