"""PluginSpec contract tests. Natural language is not production C++."""
from __future__ import annotations

from apps.grok_local_agent.factory.plugin_spec import Parameter, PluginSpec, probe_spec
from apps.grok_local_agent.factory.spec_validator import validate


def test_probe_valid():
    r = validate(probe_spec())
    assert r["status"] == "VALID"
    assert r["ok"] is True


def test_duplicate_parameter_ids():
    spec = probe_spec()
    spec.parameters.append(Parameter("GAIN", "Gain2"))
    r = validate(spec)
    assert r["status"] == "INVALID"
    assert any("duplicate" in e for e in r["errors"])


def test_default_outside_range():
    spec = probe_spec()
    spec.parameters[0].default = 99.0
    r = validate(spec)
    assert r["status"] == "INVALID"


def test_schema_version_one():
    spec = probe_spec()
    assert spec.schema_version == 1
    spec.schema_version = 99
    r = validate(spec)
    assert r["status"] == "INVALID"


def test_min_gt_max():
    spec = probe_spec()
    spec.parameters[0].min = 4.0
    spec.parameters[0].max = 0.1
    r = validate(spec)
    assert r["status"] == "INVALID"


if __name__ == "__main__":
    failed = 0
    for fn in [test_probe_valid, test_duplicate_parameter_ids, test_default_outside_range,
               test_schema_version_one, test_min_gt_max]:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)
