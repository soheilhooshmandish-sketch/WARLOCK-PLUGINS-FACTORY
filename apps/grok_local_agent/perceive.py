from dataclasses import dataclass

from .aliases import normalize
from .tools import extract_path


@dataclass
class Perception:
    raw: str
    text: str
    key: str
    path: str | None
    short: bool
    wants_write: bool


def perceive(message: str) -> Perception:
    raw = message.strip()
    text = normalize(raw)
    key = " ".join(text.lower().replace("\u200c", " ").split())
    return Perception(
        raw=raw,
        text=text,
        key=key,
        path=extract_path(text),
        short=any(w in key for w in ("کوتاه", "short", "voice")),
        wants_write=any(w in key for w in ("بنویس", "write", "delete", "حذف", "commit")),
    )
