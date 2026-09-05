from . import tools as T
from .ast_summary import summarize_python
from .knowledge import FACTS


def keywords(text: str) -> list[str]:
    stop = {"the", "and", "for", "با", "از", "به", "که", "این", "را"}
    return [w for w in text.lower().replace("/", " ").split() if len(w) > 2 and w not in stop][:6]


def auto_context(text: str) -> str:
    parts = [FACTS]
    keys = keywords(text)
    if keys:
        parts.append("name hits:\n" + T.search_names(keys[0], limit=12))
        parts.append("text hits:\n" + T.search_text(keys[0], limit=8))
    path = T.extract_path(text)
    if path and path.endswith(".py") and not T.protected(path):
        try:
            parts.append(summarize_python(path))
        except Exception as exc:
            parts.append(str(exc))
    return "\n\n".join(parts)
