from .config import AGENT_NAME, AGENT_PORT, AGENT_VERSION

FACTS = f"""{AGENT_NAME} نسخه {AGENT_VERSION}
نقش: ایجنت محلی گروک روی 127.0.0.1:{AGENT_PORT}
قفل: apps/local_agent و ChatGPT روی 8765
ابزار: فهرست، خواندن، grep، AST، git خواندنی، یادداشت، ایندکس، syntax، import، مسیرها، صدا /voice
حالت کوتاه: اگر پیام «کوتاه» یا از /voice باشد خلاصه جواب می‌دهد.
"""
