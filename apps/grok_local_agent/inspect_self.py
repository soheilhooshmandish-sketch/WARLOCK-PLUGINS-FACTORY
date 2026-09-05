import ast
import hashlib
from pathlib import Path

from .config import SELF_DIR


def _py_files() -> list[Path]:
    return sorted(p for p in SELF_DIR.glob("*.py") if p.name != "__init__.py")


def inventory() -> str:
    rows = []
    for p in _py_files():
        text = p.read_text(encoding="utf-8", errors="ignore")
        digest = hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()[:8]
        rows.append(f"{p.name:18} {len(text.splitlines()):4} ln  {digest}")
    return "Farnaz modules\n" + "\n".join(rows)


def syntax() -> str:
    bad = []
    ok = 0
    for p in _py_files():
        src = p.read_text(encoding="utf-8", errors="ignore")
        try:
            ast.parse(src)
            ok += 1
        except SyntaxError as exc:
            bad.append(f"{p.name}: {exc}")
    return "syntax FAIL\n" + "\n".join(bad) if bad else f"syntax OK ({ok} files)"


def imports() -> str:
    rows = []
    for p in _py_files():
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        mods = []
        for n in tree.body:
            if isinstance(n, ast.Import):
                mods.extend(a.name for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                mods.append("." * n.level + (n.module or ""))
        internal = [m for m in mods if m.startswith(".")]
        rows.append(f"{p.stem} -> {', '.join(internal) or '-'}")
    return "internal deps\n" + "\n".join(rows)
