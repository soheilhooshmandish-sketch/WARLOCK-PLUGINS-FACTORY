from .config import AGENT_NAME, AGENT_PORT, AGENT_VERSION

FACTS = f"""{AGENT_NAME} نسخه {AGENT_VERSION}
نقش: ایجنت محلی گروک / PowerShell روی 127.0.0.1:{AGENT_PORT}
قفل: apps/local_agent و ایجنت ChatGPT روی 8765 هرگز تغییر نمی‌کند.
حالت پیش‌فرض: آفلاین. کلید زنده باید با xai- شروع شود.
ابزار: فهرست، خواندن، جستجوی نام، جستجوی متن، خلاصه AST، git خواندنی، یادداشت در state/.
صدا: /voice در Chrome. ریشه / فقط JSON سلامت است.
"""
