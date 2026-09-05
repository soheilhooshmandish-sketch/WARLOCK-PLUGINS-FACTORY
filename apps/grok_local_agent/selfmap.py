import ast
from pathlib import Path

from .config import STATIC_DIR
from .tools import read

API_FILE = "apps/grok_local_agent/api.py"


def api_routes() -> str:
    src = read(API_FILE)
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return str(exc)
    rows = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            fn = dec.func
            name = ""
            if isinstance(fn, ast.Attribute):
                name = fn.attr
            if name not in {"get", "post", "put", "delete"}:
                continue
            path = ""
            if dec.args and isinstance(dec.args[0], ast.Constant):
                path = str(dec.args[0].value)
            rows.append(f"{name.upper():6} {path:20} -> {node.name}")
    extras = []
    if (STATIC_DIR / "voice.html").exists():
        extras.append("GET /voice  voice.html")
    if (STATIC_DIR / "index.html").exists():
        extras.append("GET /ui     index.html")
    return "Farnaz routes\n" + "\n".join(rows + extras)
