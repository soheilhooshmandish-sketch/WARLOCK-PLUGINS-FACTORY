"""Local retrieval over curated cards + live WARLOCK ledger + shared Farnaz brain."""

from .sources import CARDS, SOURCES

try:
    from .dsp_cards import CARDS as DSP_CARDS, SOURCES as DSP_SOURCES, DSP_BRAIN
except Exception:
    DSP_CARDS, DSP_SOURCES, DSP_BRAIN = [], [], ""

try:
    from .presets import cards as preset_cards
except Exception:
    def preset_cards():
        return []

STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "how", "what", "why", "with", "this", "that", "az", "be", "dar",
    "explain", "every", "all",
}
SYN = {
    "pause": "interrupt", "resume": "interrupt", "checkpoint": "checkpointer",
    "persist": "checkpointer", "hitl": "human", "approval": "approve",
    "function": "tool", "tools": "tool", "mcp": "protocol",
    "business": "warlock",
    "oversample": "dsp", "adaa": "dsp", "tanh": "dsp", "waveshape": "dsp",
    "alias": "dsp", "gate": "dsp", "morph": "dsp",
    "thall": "preset", "djent": "preset", "doom": "preset",
    "black": "preset", "ambient": "preset", "metal": "preset",
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
    deck = list(CARDS) + list(DSP_CARDS) + preset_cards() + _live_cards()
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
    urls = [s for s in list(SOURCES) + list(DSP_SOURCES) if s["topic"] in topics][:8]
    n = len(CARDS) + len(DSP_CARDS) + len(preset_cards())
    lines = [f"Farnaz local brain {n} docs. Free/OSS First. No API required."]
    if DSP_BRAIN and any(h.get("topic") == "dsp" for h in hits):
        lines.append(DSP_BRAIN)
    for h in hits:
        lines.append(f"[{h['topic']}/{h['id']}] {h['fact']}")
    if urls:
        lines.append("sources:")
        lines.extend(f"- {u['title']}: {u['url']}" for u in urls)
    return "\n\n".join(lines)


def reply(message: str) -> dict:
    return {
        "model": "grok-4.6-offline",
        "mode": "offline",
        "content": answer(message),
        "raw_id": "offline-brain",
    }
