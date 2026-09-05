from .config import AGENT_NAME, AGENT_PORT, AGENT_VERSION

FACTS = f"""{AGENT_NAME} نسخه {AGENT_VERSION}
نقش: ایجنت محلی گروک روی 127.0.0.1:{AGENT_PORT} با کنترل محدود ویندوز
قفل: apps/local_agent و ChatGPT روی 8765 — هرگز استارت/استاپ/کیل نمی‌شود
ویندوز (فقط لوکال): سیستم، پروسس، دیسک، کلیپ‌بورد، اسکرین‌شات، نوتیف، باز کردن notepad/calc/explorer/paint
خطرناک (shutdown/kill/اسکریپت آزاد) فقط با کلمه تأیید
مغز: بازیابی منابع + ابزار فایل + ویندوز
صدا: /voice
"""
