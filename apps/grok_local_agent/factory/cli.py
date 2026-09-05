"""CLI: python -m apps.grok_local_agent.factory.cli <cmd>"""
from __future__ import annotations

import json
import sys

from ..backup_gate import snapshot
from ..config import AGENT_VERSION
from .adapter import generate
from .factory_jobs import get, latest, set_state
from .licenses import dump as licenses
from .pipeline import slice_probe
from .spec import probe_spec
from .toolchain import detect, summary


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    cmd = (args[0] if args else "status").lower()
    out: dict
    if cmd in {"status", "tools"}:
        out = {"version": AGENT_VERSION, "tools": detect() if cmd == "tools" else summary()}
    elif cmd == "create":
        out = generate(probe_spec())
    elif cmd == "analyze":
        from ..audio_lab import analyze
        path = args[1] if len(args) > 1 else None
        out = analyze(path) if path else {"ok": False, "error": "wav path required"}
    elif cmd == "build":
        out = slice_probe(args[1] if len(args) > 1 else "unknown", "cli")
    elif cmd == "validate":
        from .pluginval_parse import run
        out = run(args[1]) if len(args) > 1 else {"ok": False, "error": "vst3 path required"}
    elif cmd == "package":
        from .packager import prepare
        from pathlib import Path
        out = prepare(Path("output/WARLOCK-Probe"), Path(args[1]) if len(args) > 1 else None)
    elif cmd == "resume":
        job = latest()
        out = job or {"ok": False, "error": "no job"}
    elif cmd == "rollback":
        job = latest()
        out = set_state(job["job_id"], "ROLLED_BACK") if job else {"ok": False, "error": "no job"}
    elif cmd == "doctor":
        from .doctor import report
        out = report()
    elif cmd == "gate":
        from .release_gate import evaluate
        out = evaluate()
    elif cmd == "licenses":
        out = licenses()
    elif cmd == "backup":
        out = snapshot("cli")
    else:
        out = {"ok": False, "error": "unknown command", "cmds": [
            "status", "tools", "doctor", "create", "analyze", "build", "validate", "package", "resume", "rollback",
        ]}
    print(json.dumps(out, ensure_ascii=False, indent=2)[:8000])
    return 0 if out.get("ok", True) is not False else 1


if __name__ == "__main__":
    raise SystemExit(main())
