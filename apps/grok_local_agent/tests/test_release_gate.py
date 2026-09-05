from apps.grok_local_agent.factory.release_gate import evaluate, from_artifacts
from apps.grok_local_agent.factory.project_lock import acquire, release, repair_tick, MAX_REPAIR_ATTEMPTS
from apps.grok_local_agent.killswitch import halt, resume


def test_not_run_blocks():
    r = evaluate()
    assert r["decision"] == "RELEASE_BLOCKED"
    assert "BUILD" in r["blocked"]
    assert "PLUGIN_VALIDATION" in r["blocked"]


def test_python_golden_is_not_audio_test():
    r = from_artifacts(None, None, {"ok": True, "source": "python-model"}, None)
    assert r["gates"]["AUDIO_TEST"] == "NOT_RUN"
    assert r["decision"] == "RELEASE_BLOCKED"


def test_kill_switch_blocks():
    halt("gate-test")
    r = evaluate({"PLUGINSPEC": "PASS"})
    resume()
    assert r["decision"] == "RELEASE_BLOCKED"
    assert r["reason"] == "kill switch"


def test_project_lock_and_repair_limit():
    a = acquire("probe", "job1")
    assert a["ok"] is True
    b = acquire("probe", "job2")
    assert b["ok"] is False
    release("probe", "job1")
    c = acquire("probe", "job3")
    assert c["ok"] is True
    for _ in range(MAX_REPAIR_ATTEMPTS):
        assert repair_tick("probe")["ok"] is True
    stop = repair_tick("probe")
    assert stop["stop"] is True
    release("probe", "job3")


if __name__ == "__main__":
    failed = 0
    for fn in [test_not_run_blocks, test_python_golden_is_not_audio_test,
               test_kill_switch_blocks, test_project_lock_and_repair_limit]:
        try:
            fn(); print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1; print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)
