import json
from pathlib import Path

from apps.grok_local_agent.dsp_cards import CARDS, DSP_BRAIN

NEED = {
    "dsp-adaa-stable", "dsp-clip-alts", "dsp-freq",
    "dsp-overlap-save", "dsp-ir", "mix-energy",
}


def test_shared_brain_has_pushed_cards():
    ids = {c["id"] for c in CARDS}
    missing = NEED - ids
    assert not missing, missing
    blob = (DSP_BRAIN + " ".join(c["fact"] for c in CARDS)).lower()
    for needle in ("overlap-save", "ln(cosh", "partitioned", "stft"):
        assert needle in blob, needle
    p = Path("apps/shared/farnaz_brain.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "1.1"


if __name__ == "__main__":
    test_shared_brain_has_pushed_cards()
    print("PASS test_shared_brain_has_pushed_cards")
