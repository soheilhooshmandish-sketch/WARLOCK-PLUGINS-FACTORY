"""Known-good toolchain. Do not silently upgrade."""
from __future__ import annotations

LOCK = {
    "dpf": {"version": "unpinned-until-first-green-build", "status": "UNVERIFIED"},
    "cmake": {"version": ">=3.15", "status": "UNVERIFIED"},
    "clang": {"version": "unverified", "status": "UNVERIFIED"},
    "pluginval": {"version": "unverified", "status": "UNVERIFIED"},
    "nsis": {"version": "3", "status": "UNVERIFIED"},
    "python": {"version": "3.10+", "status": "AVAILABLE"},
}


def dump() -> dict:
    return {"ok": True, "upgrade_policy": "BACKUP→TEST→BUILD→VALIDATE→REGRESSION→APPROVE", "lock": LOCK}
