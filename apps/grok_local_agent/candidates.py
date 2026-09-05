"""AutoGen-style candidate_func: shrink who the selector may pick.

If it returns one name, speak that agent (no LLM needed).
If it returns [] , the turn is skipped / terminated.
"""
from .policy import is_locked
from .selector import ROLES


def candidate_func(task: str, spoken: list[str]) -> list[str]:
    key = task.lower()
    pool = list(ROLES)

    if is_locked(task) or "apps/local_agent" in key:
        return ["reviewer"]

    if any(w in key for w in ("جستجو", "find", "search")):
        pool = ["scout"]
    elif any(w in key for w in ("syntax", "ماژول")):
        pool = ["analyst"]
    elif any(w in key for w in ("fleet", "ناوگان")):
        pool = ["fleet"]

    remaining = [n for n in pool if n not in spoken]
    return remaining or (["reviewer"] if "reviewer" not in spoken else [])
