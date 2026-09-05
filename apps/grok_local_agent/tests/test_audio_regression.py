from apps.grok_local_agent.factory.audio_regression import (
    approve_baseline, compare, factory_test_vector,
)
from apps.grok_local_agent.factory.golden import process


def test_compare_pass_against_approved():
    vec = factory_test_vector()
    out = process(vec, gain=1.0, output=1.0)["samples"]
    approve_baseline(out, "factory_test", "unit-test explicit")
    r = compare(out, "factory_test")
    assert r["status"] == "PASS"


def test_unexpected_change():
    vec = factory_test_vector()
    gold = process(vec, gain=1.0, output=1.0)["samples"]
    approve_baseline(gold, "factory_test_delta", "unit-test explicit")
    changed = process(vec, gain=4.0, output=1.0)["samples"]
    r = compare(changed, "factory_test_delta")
    assert r["status"] in {"UNEXPECTED_CHANGE", "FAIL"}
    r2 = compare(changed, "factory_test_delta", expected_change=True)
    assert r2["status"] == "EXPECTED_CHANGE"


def test_missing_ref_does_not_auto_write():
    r = compare([0.0, 0.1], "no_such_ref_ever")
    assert r["status"] == "FAIL"
    assert "silently" in r["note"]


if __name__ == "__main__":
    failed = 0
    for fn in [test_compare_pass_against_approved, test_unexpected_change, test_missing_ref_does_not_auto_write]:
        try:
            fn(); print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1; print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)
