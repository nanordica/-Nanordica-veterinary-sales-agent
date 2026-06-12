"""Persisted map of friendly names -> Pipedrive hashed field keys and stage ids.
Written by scripts/pipedrive_setup.py, read by tools and guardrails."""
import os
import json
from pathlib import Path

_EMPTY = {"pipeline_id": None, "stage_ids": {}, "field_keys": {}}


def _path() -> Path:
    return Path(os.getenv("FIELD_MAP_PATH", "./data/field_keys.json"))


def load_field_map() -> dict:
    p = _path()
    if not p.exists():
        return dict(_EMPTY)
    return json.loads(p.read_text(encoding="utf-8"))


def save_field_map(data: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_field_key(name: str) -> str | None:
    return load_field_map().get("field_keys", {}).get(name)


def resolve_stage_id(name: str) -> int | None:
    return load_field_map().get("stage_ids", {}).get(name)
