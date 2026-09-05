from .config import AGENT_NAME, AGENT_PORT, AGENT_VERSION

QA = [
    (("پورت", "port"), f"{AGENT_NAME} روی {AGENT_PORT} است. ایجنت اصلی ChatGPT روی 8765 است."),
    (("chatgpt", "اصلی", "8765"), "apps/local_agent قفل است و تغییر نمی‌کند."),
    (("اسم", "name", "کی"), f"من {AGENT_NAME} هستم، نسخه {AGENT_VERSION}."),
    (("آفلاین", "offline", "api"), "حالت پیش‌فرض آفلاین است. کلید زنده باید با xai- شروع شود."),
    (("صدا", "voice"), "صحبت با فرناز: http://127.0.0.1:8766/voice در Chrome."),
]


def answer(text: str) -> str | None:
    key = text.lower()
    hits = [msg for words, msg in QA if any(w in key for w in words)]
    return "\n".join(dict.fromkeys(hits)) if hits else None
