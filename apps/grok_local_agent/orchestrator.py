"""In-process roles. Does not start, stop, or edit apps/local_agent."""

from . import inspect_self as S
from . import stats as ST
from . import tools as T
from .peers import fleet
from .selfmap import api_routes


def scout(query: str) -> str:
    hits = T.search_names(query or "farnaz", limit=8)
    grep = T.search_text(query or "Farnaz", limit=6)
    return f"[scout]\n{hits}\n{grep}"


def analyst() -> str:
    return "[analyst]\n" + S.inventory() + "\n" + S.syntax()


def critic() -> str:
    return "[critic]\n" + ST.lock_ok() + "\noriginal agent is never modified"


def conductor(query: str) -> str:
    parts = [
        "[conductor] Farnaz 3.1 orchestration",
        fleet(),
        scout(query),
        analyst(),
        critic(),
        "[routes]\n" + api_routes(),
    ]
    return "\n\n".join(parts)
