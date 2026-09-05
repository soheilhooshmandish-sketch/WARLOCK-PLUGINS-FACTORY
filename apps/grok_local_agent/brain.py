"""Local retrieval over curated cards. Not a live LLM."""

from .sources import CARDS, SOURCES

STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "how", "what", "why", "with", "this", "that", "از", "به", "در", "که", "را",
    "یک", "چی", "چیست", "توضیح", "explain", "بگو", "کن", "کنی",
}


def _tok(text: str) -> set[str]:
    raw = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return {w for w in raw.split() if len(w) > 2 and w not in STOP}


def retrieve(query: str, k: int = 4) -> list[dict]:
    q = _tok(query)
    if not q:
        return CARDS[:k]
    scored = []
    for card in CARDS:
        hay = _tok(card["id"] + " " + card["topic"] + " " + card["tags"] + " " + card["fact"])
        score = len(q & hay)
        if card["topic"] in query.lower():
            score += 2
        if score:
            scored.append((score, card))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:k]] or CARDS[:k]


def answer(query: str) -> str:
    hits = retrieve(query)
    topics = {h["topic"] for h in hits}
    urls = [s for s in SOURCES if s["topic"] in topics][:6]
    lines = ["Farnaz brain (retrieval, not live Grok)"]
    for h in hits:
        lines.append(f"[{h['topic']}/{h['id']}] {h['fact']}")
    if urls:
        lines.append("sources:")
        lines.extend(f"- {u['title']}: {u['url']}" for u in urls)
    return "\n\n".join(lines)
