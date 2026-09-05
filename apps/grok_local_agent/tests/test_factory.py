"""Factory architecture tests. Do not claim a VST3 that was not built."""
from __future__ import annotations

from apps.grok_local_agent.config import AGENT_VERSION, PROTECTED_PATHS
from apps.grok_local_agent.factory.adapter import generate
from apps.grok_local_agent.factory.factory_jobs import STATES, create, get, set_state
from apps.grok_local_agent.factory.licenses import dump
from apps.grok_local_agent.factory.pluginval_parse import parse
from apps.grok_local_agent.factory.spec import probe_spec
from apps.grok_local_agent.factory.toolchain import detect, summary
from apps.grok_local_agent.factory.frameworks.iplug2_gen import generate as iplug_gen


def test_protected():
    assert "apps/local_agent" in PROTECTED_PATHS


def test_toolchain_structure():
    d = detect()
    assert d["install_without_permission"] is False
    assert "cmake" in d["tools"]
    assert "dpf" in d["tools"]
    s = summary()
    assert s["cmake"] in {"available", "missing"}


def test_spec_not_thall():
    spec = probe_spec()
    assert spec.plugin == "WARLOCK Factory Test"
    assert spec.framework == "DPF"
    assert "THALL" not in spec.plugin
    assert spec.validate()["ok"] is True
    ids = [p.id for p in spec.parameters]
    assert ids == ["GAIN", "OUTPUT", "BYPASS"]


def test_dpf_generator_writes_sources():
    spec = probe_spec()
    out = generate(spec)
    assert out["ok"] is True
    assert any(f.endswith("ProbeDSP.cpp") for f in out["files"])
    assert any(f.endswith("warlock-plugin.json") for f in out["files"])
    assert any(f.endswith("DistrhoPluginInfo.h") for f in out["files"])


def test_iplug_not_default():
    r = iplug_gen(probe_spec())
    assert r["ok"] is False


def test_factory_job_resume():
    job = create("WARLOCK Probe", starting_git_sha="abc")
    assert job["current_state"] == "CREATED"
    upd = set_state(job["job_id"], "WAITING_PERMISSION")
    assert upd["current_state"] == "WAITING_PERMISSION"
    loaded = get(job["job_id"])
    assert loaded["plugin_name"] == "WARLOCK Probe"
    assert "DONE" in STATES


def test_pluginval_parser():
    ok = parse("All tests passed\n", 0)
    assert ok["ok"] is True
    bad = parse("FAILED strictness\n", 1)
    assert bad["ok"] is False


def test_licenses_no_blocked_in_binary_list():
    d = dump()
    assert d["blocked"] == []
    pluginval = next(i for i in d["items"] if i["name"] == "pluginval")
    assert pluginval["linked_into_binary"] is False
    juce = next(i for i in d["items"] if i["name"] == "JUCE")
    assert juce["commercial_review_status"] == "REVIEW_REQUIRED"


def test_version_factory():
    assert AGENT_VERSION.startswith("4.")


def test_parameter_migration():
    from apps.grok_local_agent.factory.migration import migrate
    r = migrate({"params": {"GAIN": 1.5}})
    assert r["ok"] is True
    assert "OUTPUT" in r["params"] and "BYPASS" in r["params"]
    assert "OUTPUT" in r["missing_filled"]


def test_golden_python_model_not_a_vst():
    from apps.grok_local_agent.factory.golden import process
    r = process([0.0, 0.5, -0.5, 2.0], gain=2.0, output=0.8)
    assert r["ok"] is True
    assert r["source"] == "python-model"
    assert r["nan_or_inf"] is False


def test_rt_safety_scan_on_generated_dsp():
    from pathlib import Path
    from apps.grok_local_agent.factory.adapter import generate
    from apps.grok_local_agent.factory.spec import probe_spec
    from apps.grok_local_agent.factory.rt_safety import scan
    generate(probe_spec())
    r = scan(Path("apps/grok_local_agent/factory/probe/ProbeDSP.cpp"))
    assert r["ok"] is True


def test_gates_block_without_artifacts():
    from apps.grok_local_agent.factory.gates import evaluate
    g = evaluate(None, None, {"ok": True, "source": "python-model"}, None, True)
    assert g["ok"] is False
    assert "BUILD" in g["blocked"] or "BUILD_PASS" in g["blocked"]
    assert "AUDIO_TEST" in g["blocked"] or "AUDIO_TEST_PASS" in g["blocked"]


def test_checksum_missing_is_not_success():
    from pathlib import Path
    from apps.grok_local_agent.factory.checksums import sha256
    r = sha256(Path("no-such-file.vst3"))
    assert r["ok"] is False


def test_doctor_does_not_install():
    from apps.grok_local_agent.factory.doctor import report
    d = report()
    assert "missing_required" in d
    assert d["parts"]["chatgpt_agent_present"] == "HEALTHY"
    assert d["parts"]["protected"] == "HEALTHY"


if __name__ == "__main__":
    failed = 0
    for fn in [
        test_protected, test_toolchain_structure, test_spec_not_thall,
        test_dpf_generator_writes_sources, test_iplug_not_default,
        test_factory_job_resume, test_pluginval_parser, test_licenses_no_blocked_in_binary_list,
        test_version_factory, test_parameter_migration, test_golden_python_model_not_a_vst,
        test_rt_safety_scan_on_generated_dsp, test_gates_block_without_artifacts,
        test_checksum_missing_is_not_success, test_doctor_does_not_install,
    ]:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)



if __name__ == "__main__":
    failed = 0
    for fn in [
        test_protected, test_toolchain_structure, test_spec_not_thall,
        test_dpf_generator_writes_sources, test_iplug_not_default,
        test_factory_job_resume, test_pluginval_parser, test_licenses_no_blocked_in_binary_list,
        test_version_factory,
    ]:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)
