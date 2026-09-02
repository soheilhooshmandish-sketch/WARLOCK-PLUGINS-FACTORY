from __future__ import annotations

import os
import runpy
import site
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = PROJECT_ROOT / ".venv"
VENV_SITE_PACKAGES = VENV_DIR / "Lib" / "site-packages"


def activate_project_environment() -> None:
    """Recreate the important runtime effects of the project venv.

    The physical Python interpreter is launched directly to avoid the Windows
    Python 3.14 venv-launcher handoff under Task Scheduler. Processing the
    venv site-packages directory through site.addsitedir preserves .pth startup
    hooks (notably for packages such as pywin32) rather than merely appending
    the directory through PYTHONPATH.
    """
    if not VENV_SITE_PACKAGES.is_dir():
        raise RuntimeError(f"Virtual-environment site-packages not found: {VENV_SITE_PACKAGES}")

    os.environ["VIRTUAL_ENV"] = str(VENV_DIR)
    scripts = str(VENV_DIR / "Scripts")
    current_path = os.environ.get("PATH", "")
    if not current_path.lower().startswith(scripts.lower() + os.pathsep):
        os.environ["PATH"] = scripts + os.pathsep + current_path

    site.addsitedir(str(VENV_SITE_PACKAGES))


def main() -> int:
    activate_project_environment()

    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m apps.runtime_child <module> [args ...]")

    module_name = sys.argv[1]
    module_args = sys.argv[2:]
    sys.argv = [module_name, *module_args]
    runpy.run_module(module_name, run_name="__main__", alter_sys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
