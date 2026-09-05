"""Local WARLOCK business ledger. Not SAP. Lives in Farnaz state only."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .config import STATE_DIR

LEDGER = STATE_DIR / "biz.json"

SEED = {
    "company": {
        "name": "WARLOCK Plugins Factory",
        "owner": "Soheil",
        "pitch": "Boutique audio plugins. Thall is the flagship native VST line.",
        "rule": "Never modify the original ChatGPT agent on 8765.",
        "stack": "Farnaz 8766 grok-offline, original agent 8765 locked, MCP probe 8790",
    },
    "catalog": [
        {"sku": "THALL", "name": "Warlock Thall", "kind": "VST3/native", "status": "in-dev"},
        {"sku": "S01", "name": "Series 01", "kind": "product schema", "status": "design"},
    ],
    "customers": [],
    "tasks": [],
    "quotes": [],
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load() -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not LEDGER.exists():
        save(SEED)
        return json.loads(json.dumps(SEED))
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    for k, v in SEED.items():
        data.setdefault(k, v)
    return data


def save(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def briefing() -> str:
    d = load()
    c = d["company"]
    open_tasks = [t for t in d["tasks"] if t.get("status") != "done"]
    lines = [
        f"{c['name']} — {c['pitch']}",
        f"owner: {c['owner']}",
        f"rule: {c['rule']}",
        f"stack: {c['stack']}",
        f"catalog: {len(d['catalog'])} | customers: {len(d['customers'])} | open tasks: {len(open_tasks)} | quotes: {len(d['quotes'])}",
        "products:",
    ]
    for p in d["catalog"]:
        lines.append(f"  {p['sku']} {p['name']} ({p['kind']}) {p['status']}")
    if open_tasks:
        lines.append("next tasks:")
        for t in open_tasks[:8]:
            lines.append(f"  [{t['id']}] {t['title']}")
    return "\n".join(lines)


def add_customer(text: str) -> str:
    payload = re.sub(r"^(مشتری|customer)\s*[:\-]?\s*", "", text, flags=re.I).strip()
    if not payload:
        return list_customers()
    d = load()
    cid = f"C{len(d['customers'])+1:03d}"
    d["customers"].append({"id": cid, "name": payload, "at": _now()})
    save(d)
    return f"customer {cid} saved: {payload}"


def list_customers() -> str:
    d = load()
    if not d["customers"]:
        return "no customers. say: مشتری NAME"
    return "customers:\n" + "\n".join(f"{c['id']} {c['name']}" for c in d["customers"][-20:])


def add_task(text: str) -> str:
    payload = re.sub(r"^(کار|task)\s*[:\-]?\s*", "", text, flags=re.I).strip()
    if not payload:
        return list_tasks()
    d = load()
    tid = f"T{len(d['tasks'])+1:03d}"
    d["tasks"].append({"id": tid, "title": payload, "status": "open", "at": _now()})
    save(d)
    return f"task {tid} open: {payload}"


def list_tasks() -> str:
    d = load()
    if not d["tasks"]:
        return "no tasks. say: کار TITLE"
    return "tasks:\n" + "\n".join(
        f"{t['id']} {t['status']} {t['title']}" for t in d["tasks"][-20:]
    )


def add_quote(text: str) -> str:
    payload = re.sub(r"^(فاکتور|quote|invoice)\s*[:\-]?\s*", "", text, flags=re.I).strip()
    if not payload:
        return list_quotes()
    d = load()
    qid = f"Q{len(d['quotes'])+1:03d}"
    d["quotes"].append({"id": qid, "text": payload, "status": "draft", "at": _now()})
    save(d)
    return f"quote {qid} draft: {payload}"


def list_quotes() -> str:
    d = load()
    if not d["quotes"]:
        return "no quotes. say: فاکتور customer SKU price"
    return "quotes:\n" + "\n".join(
        f"{q['id']} {q['status']} {q['text']}" for q in d["quotes"][-20:]
    )


def catalog() -> str:
    d = load()
    return "catalog:\n" + "\n".join(
        f"{p['sku']} {p['name']} {p['kind']} {p['status']}" for p in d["catalog"]
    )


def funnel() -> str:
    d = load()
    return (
        f"funnel\nleads/customers: {len(d['customers'])}\n"
        f"open work: {sum(1 for t in d['tasks'] if t.get('status')!='done')}\n"
        f"draft quotes: {sum(1 for q in d['quotes'] if q.get('status')=='draft')}\n"
        "stage: build Thall → demo → quote → ship. Original ChatGPT agent stays frozen."
    )


def route(text: str) -> str:
    key = text.lower()
    if any(w in key for w in ("مشتری", "customer")):
        if key.strip() in {"مشتری", "customers", "مشتری‌ها"} or key.endswith("ها"):
            return list_customers()
        return add_customer(text)
    if any(w in key for w in ("کارها", "tasks")):
        return list_tasks()
    if key.startswith("کار ") or key.startswith("task "):
        return add_task(text)
    if any(w in key for w in ("فاکتور", "quote", "invoice")):
        if key.strip() in {"فاکتور", "quotes"}:
            return list_quotes()
        return add_quote(text)
    if any(w in key for w in ("محصول", "catalog", "sku")):
        return catalog()
    if any(w in key for w in ("قیف", "funnel", "pipeline")):
        return funnel()
    return briefing()
