import json
from datetime import datetime, timezone

from .config import PROJECT_ROOT


AUDIT_DIR = PROJECT_ROOT / ".warlock"
AUDIT_LOG = AUDIT_DIR / "audit.jsonl"


def write_audit(
    operation: str,
    status: str,
    details: dict | None = None,
) -> None:
    AUDIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "status": status,
        "details": details or {},
    }

    with AUDIT_LOG.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )