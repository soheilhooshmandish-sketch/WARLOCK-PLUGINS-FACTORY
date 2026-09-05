"""What Farnaz looks for inside each app. Local, no API."""

PROFILES = {
    "visual_studio": {
        "processes": ["devenv", "ServiceHub"],
        "title_has": ["Visual Studio", "Microsoft Visual Studio"],
        "look_for": ["Build", "Rebuild", "Error List", "Output", "Debug", "failed", "error C"],
        "click": {
            "build": "Build Solution",
            "rebuild": "Rebuild Solution",
            "error_list": "Error List",
        },
        "fail_hints": ["Build failed", "error C", "LNK", "unresolved"],
    },
    "fl_studio": {
        "processes": ["FL64", "FL", "FL64.exe"],
        "title_has": ["FL Studio"],
        "look_for": ["Channel Rack", "Mixer", "Playlist", "Piano roll"],
        "click": {},
        "note": "FL Studio is a custom canvas. UI Automation often empty. Screenshot + title only.",
    },
    "explorer": {
        "processes": ["explorer"],
        "title_has": ["File Explorer", "Explorer"],
        "look_for": ["Address", "Name", "Date modified"],
        "click": {"up": "Up", "back": "Back"},
    },
    "browser": {
        "processes": ["chrome", "msedge", "firefox", "brave"],
        "title_has": ["Chrome", "Edge", "Firefox", "Grok"],
        "look_for": ["Address", "New tab", "Reload"],
        "click": {},
    },
    "warlock_lab": {
        "processes": ["python", "node"],
        "title_has": ["WARLOCK", "Farnaz"],
        "look_for": ["SOUND", "BUILD", "FARNAZ", "THALL"],
        "click": {},
    },
}


def match_title(title: str, process: str = "") -> list[str]:
    hits = []
    t = (title or "").lower()
    p = (process or "").lower()
    for name, prof in PROFILES.items():
        if any(x.lower() in p for x in prof["processes"] if p):
            hits.append(name)
            continue
        if any(x.lower() in t for x in prof["title_has"]):
            hits.append(name)
    return hits
