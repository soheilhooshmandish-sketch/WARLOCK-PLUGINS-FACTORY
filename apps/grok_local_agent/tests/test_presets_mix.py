from apps.grok_local_agent.presets import NAMES, get, load

AXES = ("attack", "density", "frost", "sludge", "chainsaw", "sag", "hiss", "sustain")
IDS = ("LOW_CUT", "TIGHT", "BODY", "GAIN", "MORPH", "BITE", "AIR", "GATE", "SPACE", "MASTER", "OVERSAMPLING")


def test_all_banks_mix_ready():
    data = load()
    assert data["parameter_ids"] == list(IDS)
    for name in NAMES:
        bank = get(name)
        assert bank, name
        for ax in AXES:
            v = bank["energy"][ax]
            assert 0 <= v <= 100, (name, ax)
        mix = bank["mix"]
        assert mix.get("slot")
        assert "headroom_db" in mix
        assert mix.get("trim")


def test_aliases():
    assert get("HM2")["family"].startswith("stockholm")
    assert get("FUZZ")["energy"]["sag"] >= 90
    assert get("DEATH")["energy"]["chainsaw"] >= 50


def test_energy_contrast():
    assert get("BLACK_METAL")["energy"]["frost"] > get("DOOM")["energy"]["frost"]
    assert get("STONER")["energy"]["sag"] > get("DJENT")["energy"]["sag"]
    assert get("DEATH_HM2")["energy"]["chainsaw"] > get("THALL")["energy"]["chainsaw"]
    assert get("DJENT")["gate"] > get("STONER")["gate"]


if __name__ == "__main__":
    failed = 0
    for fn in [test_all_banks_mix_ready, test_aliases, test_energy_contrast]:
        try:
            fn(); print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1; print("FAIL", fn.__name__, exc)
    raise SystemExit(failed)
