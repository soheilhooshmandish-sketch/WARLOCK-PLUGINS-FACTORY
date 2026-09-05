REPLACEMENTS = {
    "fehrest": "فهرست",
    "kholase": "خلاصه",
    "khoalse": "خلاصه",
    "komak": "کمک",
    "gitstatus": "git status",
    "serch": "جستجو",
    "seach": "جستجو",
    "healh": "health",
    "healty": "health",
}


def normalize(text: str) -> str:
    out = text
    low = text.lower()
    for src, dst in REPLACEMENTS.items():
        if src in low:
            out = out.replace(src, dst).replace(src.title(), dst)
    return out
