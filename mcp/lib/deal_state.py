"""All deal metadata lives in one JSON custom field (constants.STATE_FIELD_NAME).
Helpers to read it from a raw deal dict and encode updates into a write body."""
import json
from lib.field_map import resolve_field_key
from lib.constants import STATE_FIELD_NAME


def state_key() -> str | None:
    """Resolve the hashed Pipedrive key of the JSON state field (or None)."""
    return resolve_field_key(STATE_FIELD_NAME)


def read_state(deal: dict) -> dict:
    """Parse the JSON state dict from a raw deal dict. {} if absent/blank/bad."""
    key = state_key()
    raw = deal.get(key) if key else None
    if not raw:
        return {}
    try:
        val = json.loads(raw)
        return val if isinstance(val, dict) else {}
    except (ValueError, TypeError):
        return {}


def encode_state(data: dict) -> dict:
    """Return a Pipedrive write body that sets the state field to JSON(data).
    Returns {} if the state field key is unknown (setup not run yet)."""
    key = state_key()
    if not key:
        return {}
    return {key: json.dumps(data, ensure_ascii=False)}
