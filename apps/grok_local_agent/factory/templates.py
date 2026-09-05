"""Verified templates later. First slice is utility/factory-test only."""

ORDER = (
    "utility",  # WARLOCK Factory Test — current slice
    "noise_gate",
    "distortion",
    "eq",
    "delay",
    "reverb",
    "multifx",
    "thall",  # last — existing JUCE knowledge, do not auto-migrate
)

LOCKED = ("thall",)


def next_after_probe() -> str:
    return "noise_gate"
