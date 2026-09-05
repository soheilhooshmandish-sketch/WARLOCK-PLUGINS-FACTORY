import re
from .config import MAX_CONTENT

SECRET = re.compile(r"(xai-[A-Za-z0-9_-]{8,}|Bearer\s+\S+|WARLOCK_[A-Z_]*TOKEN\s*=\s*\S+)", re.I)


def redact(text: str) -> str:
    return SECRET.sub("[redacted]", text)


def trim(text: str) -> str:
    if len(text) <= MAX_CONTENT:
        return text
    return text[:MAX_CONTENT] + "\n…critic truncated"


def review(chunks: list[str], short: bool) -> str:
    if short:
        chunks = [c[:280] for c in chunks[:2]]
    return trim(redact("\n\n".join(chunks)))
