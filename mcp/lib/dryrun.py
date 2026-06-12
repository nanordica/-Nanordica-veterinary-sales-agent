"""Global DRY_RUN switch. When on, write tools log intent and skip the API."""
import os
import json
import logging

logger = logging.getLogger("ravimus.dryrun")


def is_dry_run() -> bool:
    """True unless DRY_RUN is explicitly 0/false/empty. Defaults to ON."""
    return os.getenv("DRY_RUN", "1").strip().lower() not in ("0", "false", "")


def dry_log(action: str, **details) -> dict:
    """Log a would-be write and return a simulated-success marker."""
    logger.info("DRY_RUN %s %s", action,
                json.dumps(details, ensure_ascii=False, default=str))
    return {"dry_run": True, "action": action, "details": details}
