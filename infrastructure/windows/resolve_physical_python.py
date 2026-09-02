from __future__ import annotations

import ctypes
import sys
from pathlib import Path


def physical_python_executable() -> Path:
    """Return the physical interpreter image behind a Windows venv launcher."""
    if sys.platform != "win32":
        return Path(sys.executable).resolve()

    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, len(buffer))
    if not length:
        raise OSError("GetModuleFileNameW failed")

    path = Path(buffer.value)
    if not path.is_file():
        raise FileNotFoundError(f"Physical Python runtime not found: {path}")
    return path


def main() -> int:
    print(physical_python_executable())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
