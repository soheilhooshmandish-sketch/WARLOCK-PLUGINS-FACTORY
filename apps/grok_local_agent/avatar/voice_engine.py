"""TTS abstraction. Local/free first. Brain never binds to one vendor."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from ..config import STATE_DIR
from .lip_sync import detect_lang, duration_ms, visemes_from_text, visemes_from_wav
from .settings import load as load_settings

CACHE = STATE_DIR / "tts_cache"
_stop = threading.Event()
_lock = threading.Lock()


class VoiceEngine:
    def __init__(self) -> None:
        self.backend = self._pick()

    def _pick(self) -> str:
        if "pyttsx3" in sys.modules or self._can_import("pyttsx3"):
            return "pyttsx3"
        if os.name == "nt":
            return "sapi"
        if shutil.which("espeak-ng") or shutil.which("espeak"):
            return "espeak"
        return "viseme"

    def _can_import(self, name: str) -> bool:
        try:
            __import__(name)
            return True
        except Exception:
            return False

    def stop(self) -> None:
        _stop.set()

    def interrupt(self) -> None:
        self.stop()

    def list_backends(self) -> list[str]:
        found = ["viseme"]
        if os.name == "nt":
            found.append("sapi")
        if shutil.which("espeak-ng") or shutil.which("espeak"):
            found.append("espeak")
        if self._can_import("pyttsx3"):
            found.append("pyttsx3")
        return found

    def speak(self, text: str, lang: str | None = None) -> dict:
        _stop.clear()
        text = (text or "").strip()
        if not text:
            return {"backend": self.backend, "spoken": "", "visemes": [], "duration_ms": 0, "lang": "en"}
        settings = load_settings()
        if settings.get("muted"):
            frames = visemes_from_text(text)
            return {
                "backend": "muted",
                "spoken": text,
                "visemes": frames,
                "duration_ms": duration_ms(frames),
                "lang": lang or detect_lang(text),
                "cached": False,
            }
        lang = lang or detect_lang(text)
        wav = self._synthesize(text, lang, float(settings.get("volume", 0.85)))
        if wav and Path(wav).exists():
            try:
                frames = visemes_from_wav(wav)
            except Exception:
                frames = visemes_from_text(text)
            return {
                "backend": self.backend,
                "spoken": text,
                "visemes": frames,
                "duration_ms": duration_ms(frames),
                "lang": lang,
                "wav": wav,
                "cached": True,
            }
        frames = visemes_from_text(text)
        return {
            "backend": self.backend,
            "spoken": text,
            "visemes": frames,
            "duration_ms": duration_ms(frames),
            "lang": lang,
            "cached": False,
            "note": "No local TTS binary. Panel uses browser speechSynthesis.",
        }

    def _cache_path(self, text: str, lang: str) -> Path:
        CACHE.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha1(f"{self.backend}|{lang}|{text}".encode("utf-8")).hexdigest()[:16]
        return CACHE / f"{h}.wav"

    def _synthesize(self, text: str, lang: str, volume: float) -> str | None:
        dest = self._cache_path(text, lang)
        if dest.exists() and dest.stat().st_size > 44:
            return str(dest)
        with _lock:
            if self.backend == "sapi":
                return self._sapi(text, dest)
            if self.backend == "espeak":
                return self._espeak(text, lang, dest)
            if self.backend == "pyttsx3":
                return self._pyttsx3(text, dest, volume)
        return None

    def _sapi(self, text: str, dest: Path) -> str | None:
        # Local Windows SAPI. No network. Persian works only if a fa voice is installed.
        safe = dest.with_suffix(".wav")
        script = (
            "Add-Type -AssemblyName System.Speech;"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            f"$s.SetOutputToWaveFile('{safe.as_posix()}');"
            f"$s.Speak([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{_b64(text)}')));"
            "$s.Dispose();"
        )
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                check=True,
                capture_output=True,
                timeout=30,
            )
            if safe.exists() and safe.stat().st_size > 44:
                return str(safe)
        except Exception:
            return None
        return None

    def _espeak(self, text: str, lang: str, dest: Path) -> str | None:
        bin_ = shutil.which("espeak-ng") or shutil.which("espeak")
        if not bin_:
            return None
        voice = "fa" if lang == "fa" else "en"
        try:
            subprocess.run(
                [bin_, "-v", voice, "-w", str(dest), text[:800]],
                check=True,
                capture_output=True,
                timeout=20,
            )
            if dest.exists():
                return str(dest)
        except Exception:
            return None
        return None

    def _pyttsx3(self, text: str, dest: Path, volume: float) -> str | None:
        try:
            import pyttsx3
            eng = pyttsx3.init()
            eng.setProperty("volume", max(0.0, min(1.0, volume)))
            eng.save_to_file(text[:800], str(dest))
            eng.runAndWait()
            if dest.exists():
                return str(dest)
        except Exception:
            return None
        return None


def _b64(text: str) -> str:
    import base64
    return base64.b64encode(text.encode("utf-8")).decode("ascii")
