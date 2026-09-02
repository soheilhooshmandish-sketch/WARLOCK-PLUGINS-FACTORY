from __future__ import annotations

import os
import runpy
import site
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / ".warlock" / "runtime"
VENV_DIR = PROJECT_ROOT / ".venv"
VENV_SITE_PACKAGES = VENV_DIR / "Lib" / "site-packages"
CHILD_BOOTSTRAP_LOG = RUNTIME_DIR / "runtime-child.bootstrap.log"


def bootstrap_log(message: str) -> None:
    try:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with CHILD_BOOTSTRAP_LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] PID {os.getpid()} | {message}\n")
    except BaseException:
        pass


def activate_project_environment() -> None:
    """Recreate the controlled runtime effects of the project venv.

    The physical Python interpreter is launched with -S so automatic system
    and user site-package initialization is disabled. Warlock then activates
    only the project's venv site-packages here. site.addsitedir processes the
    venv's .pth files, which is required by packages such as pywin32.
    """
    bootstrap_log("activating project environment")

    if not VENV_SITE_PACKAGES.is_dir():
        raise RuntimeError(f"Virtual-environment site-packages not found: {VENV_SITE_PACKAGES}")

    os.environ["VIRTUAL_ENV"] = str(VENV_DIR)
    scripts = str(VENV_DIR / "Scripts")
    current_path = os.environ.get("PATH", "")
    if not current_path.lower().startswith(scripts.lower() + os.pathsep):
        os.environ["PATH"] = scripts + os.pathsep + current_path

    bootstrap_log(f"before addsitedir | site-packages={VENV_SITE_PACKAGES}")
    site.addsitedir(str(VENV_SITE_PACKAGES))
    bootstrap_log("after addsitedir")


def main() -> int:
    bootstrap_log(f"runtime child entered | executable={sys.executable} | argv={sys.argv!r}")
    activate_project_environment()

    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m apps.runtime_child <module> [args ...]")

    module_name = sys.argv[1]
    module_args = sys.argv[2:]
    bootstrap_log(f"before run_module | module={module_name}")
    sys.argv = [module_name, *module_args]
    runpy.run_module(module_name, run_name="__main__", alter_sys=True)
    bootstrap_log(f"module returned | module={module_name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        bootstrap_log(f"fatal {type(exc).__name__}: {exc}")
        raise
