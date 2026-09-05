"""Local retrieval over curated cards + live WARLOCK ledger."""

from .sources import CARDS, SOURCES

STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "how", "what", "why", "with", "this", "that", "از", "به", "در", "که", "را",
    "یک", "چی", "چیست", "توضیح", "explain", "بگو", "کن", "کنی", "every", "all",
}
SYN = {
    "pause": "interrupt", "resume": "interrupt", "checkpoint": "checkpointer",
    "persist": "checkpointer", "hitl": "human", "approval": "approve",
    "function": "tool", "tools": "tool", "mcp": "protocol",
    "گروک": "xai", "کلید": "xai", "قفل": "lock",
    "کسب": "warlock", "تجارت": "warlock", "business": "warlock",
    "مشتری": "customer", "فاکتور": "quote", "محصول": "thall",
}


def _tok(text: str) -> set[str]:
    raw = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    out = set()
    for w in raw.split():
        if len(w) <= 2 or w in STOP:
            continue
        out.add(w)
        if w in SYN:
            out.add(SYN[w])
    return out


def _live_cards() -> list[dict]:
    try:
        from .biz import load
        d = load()
        cards = [{
            "id": "co",
            "topic": "warlock",
            "tags": "company business warlock factory soheil thall",
            "fact": "{name}: {pitch} Owner {owner}. {rule} {stack}".format(**d["company"]),
        }]
        for p in d.get("catalog", []):
            cards.append({
                "id": p["sku"].lower(),
                "topic": "warlock",
                "tags": f"catalog product {p['sku']} {p['name']}",
                "fact": f"SKU {p['sku']} {p['name']} {p['kind']} status={p['status']}",
            })
        return cards
    except Exception:
        return []


def retrieve(query: str, k: int = 5) -> list[dict]:
    q = _tok(query)
    deck = list(CARDS) + _live_cards()
    if not q:
        return deck[:k]
    scored = []
    ql = query.lower()
    for card in deck:
        hay = _tok(card["id"] + " " + card["topic"] + " " + card["tags"] + " " + card["fact"])
        score = len(q & hay)
        if card["topic"] in ql:
            score += 3
        if card["id"] in ql.replace("_", "-"):
            score += 2
        if score:
            scored.append((score, card))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:k]] or deck[:k]


def answer(query: str) -> str:
    hits = retrieve(query)
    topics = {h["topic"] for h in hits}
    urls = [s for s in SOURCES if s["topic"] in topics][:8]
    lines = [f"Farnaz brain {len(CARDS)} docs + live ledger"]
    for h in hits:
        lines.append(f"[{h['topic']}/{h['id']}] {h['fact']}")
    if urls:
        lines.append("sources:")
        lines.extend(f"- {u['title']}: {u['url']}" for u in urls)
    return "\n\n".join(lines)
