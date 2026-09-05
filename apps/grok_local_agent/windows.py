"""Gated local Windows control. Loopback only. No unrestricted shell."""
from __future__ import annotations

import os
import platform
import socket
import subprocess
from pathlib import Path

from .config import PROJECT_ROOT, STATE_DIR
from .policy import is_locked

APPS = {
    "notepad": "notepad.exe",
    "نوتپد": "notepad.exe",
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "ماشینحساب": "calc.exe",
    "explorer": "explorer.exe",
    "فایل": "explorer.exe",
    "paint": "mspaint.exe",
    "نقاشی": "mspaint.exe",
}
DENY_KILL = {
    "csrss", "lsass", "winlogon", "services", "smss", "system", "idle", "svchost",
}
FORBID_PS = (
    "shutdown", "stop-computer", "restart-computer", "format-volume",
    "remove-item -recurse", "irm ", "iwr ", "invoke-webrequest",
    "invoke-expression", "iex ", "reg delete", "net user",
    "apps/local_agent", "stop-process -name python",
)


def approved(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in ("تأیید", "تایید", "confirm", "approve", "yes-do-it"))


def _ps(script: str, timeout: int = 20) -> str:
    if os.name != "nt":
        return "windows-only: this host is not Windows"
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        return f"powershell: {exc}"
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    return (out or f"exit {r.returncode}")[:4000]


def info() -> str:
    return (
        f"host={socket.gethostname()}\n"
        f"user={os.getenv('USERNAME') or os.getenv('USER')}\n"
        f"os={platform.platform()}\n"
        f"python={platform.python_version()}\n"
        f"cwd={os.getcwd()}\n"
        f"project={PROJECT_ROOT}"
    )


def processes() -> str:
    return _ps(
        "Get-Process | Sort-Object WorkingSet64 -Descending | "
        "Select-Object -First 15 Name,Id,@{N='MB';E={[int]($_.WorkingSet64/1MB)}} | "
        "Format-Table -Auto | Out-String"
    )


def disks() -> str:
    return _ps(
        "Get-PSDrive -PSProvider FileSystem | "
        "Select-Object Name,@{N='UsedGB';E={[math]::Round(($_.Used/1GB),1)}},"
        "@{N='FreeGB';E={[math]::Round(($_.Free/1GB),1)}} | Format-Table -Auto | Out-String"
    )


def start_app(name: str) -> str:
    exe = APPS.get(name.strip().lower())
    if not exe:
        return "allowed apps: " + ", ".join(sorted(set(APPS.values())))
    try:
        subprocess.Popen([exe], close_fds=True)
    except Exception as exc:
        return str(exc)
    return f"started {exe}"


def clip_get() -> str:
    return _ps("Get-Clipboard | Out-String") or "(empty)"


def clip_set(text: str) -> str:
    os.environ["FARNAZ_CLIP"] = text[:2000]
    return _ps("Set-Clipboard -Value $env:FARNAZ_CLIP; 'clipboard-set'")


def notify(msg: str) -> str:
    os.environ["FARNAZ_POP"] = msg[:200]
    return _ps(
        "$w=New-Object -ComObject WScript.Shell; "
        "$w.Popup($env:FARNAZ_POP,4,'Farnaz',64) | Out-Null; 'notified'"
    )


def screenshot() -> str:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    dest = STATE_DIR / "screenshot.png"
    path = str(dest).replace("'", "")
    return _ps(
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
        "$b=[Windows.Forms.SystemInformation]::VirtualScreen; "
        "$bmp=New-Object Drawing.Bitmap $b.Width,$b.Height; "
        "$g=[Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen($b.Left,$b.Top,[Drawing.Point]::Empty,$bmp.Size); "
        f"$bmp.Save('{path}'); $g.Dispose(); $bmp.Dispose(); 'saved {path}'",
        timeout=25,
    )


def open_folder(raw: str) -> str:
    target = Path(raw.strip() or str(PROJECT_ROOT))
    if not target.exists():
        return f"missing: {target}"
    rel = str(target)
    try:
        rel = target.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except Exception:
        pass
    if is_locked(rel):
        return "POLICY DENY original agent folder"
    subprocess.Popen(["explorer.exe", str(target)])
    return f"opened {target}"


def kill(name: str, text: str) -> str:
    n = name.lower().replace(".exe", "")
    if n in DENY_KILL or "local_agent" in n:
        return "POLICY DENY: protected process"
    if not approved(text):
        return "say تأیید to kill a process"
    return _ps(f"Stop-Process -Name '{n}' -ErrorAction SilentlyContinue; 'killed {n}'")


def help_win() -> str:
    return "\n".join([
        "Windows tools (127.0.0.1 only)",
        "سیستم | پروسس | دیسک | کلیپ‌بورد | اسکرین",
        "باز کن notepad | calc | explorer | paint",
        "نوتیف متن... | کلیپ بگذار ...",
        "kill NAME تأیید — shutdown/format never",
    ])


def route(text: str) -> str:
    key = text.lower()
    if any(w in key for w in ("shutdown", "restart-computer", "format", "فرمت")):
        return "POLICY DENY: power/disk destroy is disabled"
    if any(w in key for w in FORBID_PS):
        return "POLICY DENY: blocked powershell pattern"
    if any(w in key for w in ("کمک ویندوز", "windows help", "چی کنترل")):
        return help_win()
    if any(w in key for w in ("screenshot", "اسکرین", "عکس")):
        return screenshot()
    if any(w in key for w in ("پروسس", "process", "tasklist")):
        return processes()
    if any(w in key for w in ("دیسک", "disk", "drive")):
        return disks()
    if key.startswith("کلیپ بگذار") or key.startswith("clipboard set"):
        payload = text.split(" ", 2)[-1] if " " in text else ""
        return clip_set(payload)
    if any(w in key for w in ("clipboard", "کلیپ")):
        return clip_get()
    if key.startswith("نوتیف") or key.startswith("notify"):
        payload = text.split(" ", 1)[-1]
        return notify(payload)
    if key.startswith("kill ") or key.startswith("بکش "):
        name = text.split(" ", 1)[-1].split()[0]
        return kill(name, text)
    for name in APPS:
        if name in key and any(w in key for w in ("باز", "start", "open", "بکشا", "شروع")):
            return start_app(name)
    if any(w in key for w in ("باز کن پوشه", "open folder")):
        return open_folder(PROJECT_ROOT.as_posix())
    if any(w in key for w in ("سیستم", "whoami", "hostname", "windows", "ویندوز")):
        return info() + "\n\n" + help_win()
    return help_win()
