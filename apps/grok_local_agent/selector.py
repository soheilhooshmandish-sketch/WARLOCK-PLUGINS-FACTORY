"""SelectorGroupChat strategies without an LLM picker.

AutoGen SelectorGroupChat usually asks a model: who speaks next?
Offline Farnaz uses deterministic selectors instead.
"""
from . import inspect_self as S
from . import stats as ST
from . import tools as T
from .config import AUTOGEN_MAX_TURNS
from .peers import fleet
from .policy import is_locked

ROLES = ("scout", "analyst", "fleet", "reviewer")


def _scout(task: str) -> str:
    q = next((w for w in task.split() if len(w) > 3), "farnaz")
    return T.search_names(q, limit=6)


def _analyst(_: str) -> str:
    return S.syntax()


def _fleet(_: str) -> str:
    return fleet()


def _reviewer(_: str) -> str:
    return ST.lock_ok() + "\nAPPROVE"


RUN = {
    "scout": _scout,
    "analyst": _analyst,
    "fleet": _fleet,
    "reviewer": _reviewer,
}


def mention_select(text: str) -> str | None:
    key = text.lower()
    for name in ROLES:
        if f"@{name}" in key or f" {name} " in f" {key} ":
            return name
    return None


def keyword_select(text: str) -> str:
    key = text.lower()
    if is_locked(text) or any(w in key for w in ("قفل", "chatgpt", "8765", "اصلی")):
        return "reviewer"
    if any(w in key for w in ("fleet", "ناوگان", "8766", "health")):
        return "fleet"
    if any(w in key for w in ("syntax", "ماژول", "خودت", "ast")):
        return "analyst"
    if any(w in key for w in ("جستجو", "find", "search", "پیدا")):
        return "scout"
    return "scout"


def round_robin_select(last: str | None) -> str:
    if last not in ROLES:
        return ROLES[0]
    return ROLES[(ROLES.index(last) + 1) % len(ROLES)]


def select_next(text: str, last: str | None, strategy: str) -> str:
    if strategy == "mention":
        return mention_select(text) or keyword_select(text)
    if strategy == "keyword":
        return keyword_select(text)
    return round_robin_select(last)


def run_selector(task: str, strategy: str = "keyword") -> str:
    lines = [f"SelectorGroupChat strategy={strategy} max={AUTOGEN_MAX_TURNS}"]
    last = None
    spoken: list[str] = []
    for _ in range(AUTOGEN_MAX_TURNS):
        name = select_next(task, last, strategy)
        if strategy == "keyword" and name in spoken:
            break
        spoken.append(name)
        body = RUN[name](task)
        lines.append(f"[{name}] {body}")
        last = name
        if "APPROVE" in body:
            break
        if strategy == "roundrobin":
            continue
        if strategy == "keyword":
            break
    return "\n\n".join(lines)
