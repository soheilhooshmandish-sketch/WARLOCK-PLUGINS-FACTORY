from pathlib import Path
import tempfile

from apps.grok_local_agent.factory.realtime_safety import scan_file
from apps.grok_local_agent.factory.adapter import generate
from apps.grok_local_agent.factory.spec import probe_spec


def test_generated_probe_pass():
    generate(probe_spec())
    r = scan_file(Path("apps/grok_local_agent/factory/probe/ProbeDSP.cpp"))
    assert r["status"] in {"PASS", "WARNING"}
    assert r["ok"] is True


def test_detects_fopen_fail():
    text = """
void run(const float** inputs, float** outputs, uint32_t frames) {
    FILE* f = fopen("x", "w");
    (void)f;
}
"""
    p = Path(tempfile.gettempdir()) / "bad_dsp.cpp"
    p.write_text(text, encoding="utf-8")
    r = scan_file(p)
    assert r["status"] == "FAIL"
    assert any(h["rule"] == "file-io" for h in r["hits"])


if __name__ == "__main__":
    failed = 0
    for fn in [test_generated_probe_pass, test_detects_fopen_fail]:
        try:
            fn(); print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1; print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)
