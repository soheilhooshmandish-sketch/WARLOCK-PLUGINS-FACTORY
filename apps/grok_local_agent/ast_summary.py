import ast
from pathlib import Path

from .tools import protected, read


def summarize_python(path: str) -> str:
    if protected(path):
        return f"LOCKED {path}"
    raw = read(path)
    try:
        tree = ast.parse(raw)
    except SyntaxError as exc:
        return f"parse error {path}: {exc}"
    funcs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    imports = []
    for n in tree.body:
        if isinstance(n, ast.Import):
            imports.extend(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imports.append(n.module)
    return (
        f"{path}\nclasses: {', '.join(classes) or '-'}\n"
        f"funcs: {', '.join(funcs) or '-'}\n"
        f"imports: {', '.join(imports[:20]) or '-'}\n"
        f"size: {Path(path).name} {len(raw.splitlines())} lines"
    )
