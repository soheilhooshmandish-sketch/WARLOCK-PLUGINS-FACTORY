import ast
from pathlib import Path

from .config import SELF_DIR


def _py_files() -> list[Path]:
    return sorted(p for p in SELF_DIR.glob("*.py") if p.name != "__init__.py")


def inventory() -> str:
    rows = []
    for p in _py_files():
        text = p.read_text(encoding="utf-8", errors="ignore")
        rows.append(f"{p.name:18} {len(text.splitlines()):4} lines  {len(text):6} bytes")
    return "Farnaz modules\n" + "\n".join(rows)


def syntax() -> str:
    ok = []
    bad = []
    for p in _py_files():
        src = p.read_text(encoding="utf-8", errors="ignore")
        try:
            ast.parse(src)
            ok.append(p.name)
        except SyntaxError as exc:
            bad.append(f"{p.name}: {exc}")
    if bad:
        return "syntax FAIL\n" + "\n".join(bad)
    return f"syntax OK ({len(ok)} files)"


def imports() -> str:
    rows = []
    for p in _py_files():
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        mods = []
        for n in tree.body:
            if isinstance(n, ast.Import):
                mods.extend(a.name for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                mods.append(n.module)
        rows.append(f"{p.name}: {', '.join(mods[:12])}")
    return "imports\n" + "\n".join(rows)
