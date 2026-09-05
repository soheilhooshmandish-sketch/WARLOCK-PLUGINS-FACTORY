"""CPack → NSIS. Inno is not the default. No secrets in the package."""
from __future__ import annotations

import shutil
from pathlib import Path

from ..config import PROJECT_ROOT

NSIS = r"""
Name "WARLOCK Probe"
OutFile "WARLOCK-Probe-Setup.exe"
InstallDir "$COMMONFILES\VST3\WARLOCK Probe.vst3"
RequestExecutionLevel admin
Page directory
Page instfiles
Section "Install"
  SetOutPath "$INSTDIR"
  File /r "VST3\*.*"
SectionEnd
"""

CMAKE_PACK = """include(CPack)
set(CPACK_GENERATOR "NSIS")
set(CPACK_PACKAGE_NAME "WARLOCK-Probe")
set(CPACK_PACKAGE_VENDOR "WARLOCK")
set(CPACK_PACKAGE_VERSION "0.1.0")
set(CPACK_NSIS_PACKAGE_NAME "WARLOCK Probe")
"""


def prepare(release_dir: Path, vst3: Path | None) -> dict:
    release_dir.mkdir(parents=True, exist_ok=True)
    (release_dir / "README").write_text("WARLOCK Probe factory proof. Not THALL.\n", encoding="utf-8")
    (release_dir / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (release_dir / "CPackConfig.cmake.in").write_text(CMAKE_PACK, encoding="utf-8")
    (release_dir / "installer.nsi").write_text(NSIS, encoding="utf-8")
    installer = None
    nsis = shutil.which("makensis")
    cpack = shutil.which("cpack")
    if not nsis and not cpack:
        return {
            "ok": False,
            "error": "NSIS/CPack missing",
            "release_dir": str(release_dir),
            "installer": None,
            "vst3": str(vst3) if vst3 else None,
        }
    if vst3 and vst3.exists():
        dest = release_dir / "WARLOCK-Probe.vst3"
        if vst3.is_dir():
            shutil.copytree(vst3, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(vst3, dest)
    return {
        "ok": False,
        "error": "packager scripts written; installer not produced because NSIS/CPack did not run a verified build",
        "release_dir": str(release_dir),
        "installer": installer,
        "scripts": ["installer.nsi", "CPackConfig.cmake.in"],
    }
