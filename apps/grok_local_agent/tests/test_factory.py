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
    assert spec.plugin == "WARLOCK Probe"
    assert spec.framework == "DPF"
    assert "THALL" not in spec.plugin


def test_dpf_generator_writes_sources():
    spec = probe_spec()
    out = generate(spec)
    assert out["ok"] is True
    assert any(f.endswith("ProbeDSP.cpp") for f in out["files"])
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
