from apps.grok_local_agent.factory.host_matrix import auto_pluginval, record, report


def test_default_not_tested():
    r = report()
    assert r["hosts"]["FL Studio"]["result"] == "NOT_TESTED"
    assert r["hosts"]["REAPER"]["result"] == "NOT_TESTED"
    assert "FL Studio" not in r["pass"]


def test_persist_fail_not_pass():
    rec = record("Cubase", "FAIL", notes="unit")
    assert rec["result"] == "FAIL"
    r = report()
    assert r["hosts"]["Cubase"]["result"] == "FAIL"
    record("Cubase", "NOT_TESTED", notes="reset")


def test_pluginval_missing_is_not_tested():
    r = auto_pluginval(None)
    assert r["result"] == "NOT_TESTED"


if __name__ == "__main__":
    failed = 0
    for fn in [test_default_not_tested, test_persist_fail_not_pass, test_pluginval_missing_is_not_tested]:
        try:
            fn(); print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1; print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)
