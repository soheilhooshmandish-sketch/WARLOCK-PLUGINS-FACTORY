"""Static DSP guardrail. Does NOT mathematically prove realtime safety."""
from __future__ import annotations

import re
from pathlib import Path

RULES = [
    ("file-io", r"\b(fopen|ifstream|ofstream|fstream)\b", "FAIL", "file I/O in DSP"),
    ("network", r"\b(socket|connect|recv|send|http)\b", "FAIL", "network in DSP"),
    ("python", r"\b(Py_|PyObject|python_callback)\b", "FAIL", "Python callback in DSP"),
    ("sleep", r"\b(sleep|Sleep|std::this_thread::sleep)\b", "FAIL", "sleep in DSP"),
    ("process", r"\b(system|popen|execve|CreateProcess)\b", "FAIL", "process launch in DSP"),
    ("gui", r"\b(ShowWindow|MessageBox|QWidget|juce::AlertWindow)\b", "FAIL", "GUI call in DSP"),
    ("mutex", r"\b(std::mutex|std::lock_guard|WaitForSingleObject)\b", "WARNING", "blocking sync"),
    ("alloc", r"\b(new |malloc\s*\(|realloc\s*\(|std::vector\s*<)", "WARNING", "allocation in hot path"),
    ("log", r"\b(printf|cout|cerr|std::clog)\b", "WARNING", "logging in DSP"),
]


def scan_file(path: Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"status": "FAIL", "ok": False, "hits": [], "error": "missing file", "path": str(p)}
    lines = p.read_text(encoding="utf-8").splitlines()
    hits = []
    in_run = False
    for i, line in enumerate(lines, 1):
        if re.search(r"\bvoid\s+run\s*\(", line):
            in_run = True
        if in_run and line.strip().startswith("private:"):
            in_run = False
        if not in_run:
            continue
        stripped = line.split("//")[0]
        for rule, pat, sev, why in RULES:
            if re.search(pat, stripped):
                hits.append({"file": str(p), "line": i, "rule": rule, "severity": sev, "explanation": why})
    fails = [h for h in hits if h["severity"] == "FAIL"]
    warns = [h for h in hits if h["severity"] == "WARNING"]
    if fails:
        status = "FAIL"
    elif warns:
        status = "WARNING"
    else:
        status = "PASS"
    return {"status": status, "ok": status != "FAIL", "hits": hits, "path": str(p),
            "note": "Guardrail only. Not a formal RT proof. UI must not be required for DSP."}


def scan(path: Path) -> dict:
    """Compat wrapper used by older tests."""
    r = scan_file(path)
    return {"ok": r["ok"], "hits": [h["rule"] for h in r["hits"]], "path": r["path"], "status": r["status"], "note": r.get("note")}
