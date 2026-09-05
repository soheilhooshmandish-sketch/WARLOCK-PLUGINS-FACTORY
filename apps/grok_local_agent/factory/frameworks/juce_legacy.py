"""JUCE is legacy for existing THALL. New plugins do not auto-migrate."""
from __future__ import annotations


def generate(spec) -> dict:
    return {
        "ok": False,
        "framework": "LegacyJUCE",
        "error": "JUCE is not the default. Existing THALL stays. New plugins use DPF.",
        "spec": getattr(spec, "plugin", None),
    }
