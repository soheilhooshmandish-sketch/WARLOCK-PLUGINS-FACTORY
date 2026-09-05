"""Host compatibility. Untested until a real VST3 is loaded in that host."""

HOSTS = {
    "FL Studio": "untested",
    "REAPER": "untested",
    "Ableton Live": "untested",
    "Cubase": "untested",
    "Studio One": "untested",
}


def report() -> dict:
    return {
        "ok": False,
        "hosts": HOSTS,
        "note": "Do not claim host compatibility. No VST3 has been loaded in a DAW this session.",
    }
