"""Decide which registry rows become new deals: e-mail present and
syntactically valid, registry_id not seen before (in Pipedrive or earlier in
the same CSV). Expired certificates are included by design (user decision
2026-06-12); qualification scores them later."""
import re

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL.match(email or ""))


def plan_discovery(rows: list[dict], existing_ids: set[str]) -> dict:
    to_create = []
    skipped = {"existing": 0, "no_email": 0, "bad_email": 0}
    seen = set(existing_ids)
    for row in rows:
        email = (row.get("email") or "").strip()
        rid = (row.get("registry_id") or "").strip()
        if not email:
            skipped["no_email"] += 1
        elif not is_valid_email(email):
            skipped["bad_email"] += 1
        elif rid in seen:
            skipped["existing"] += 1
        else:
            seen.add(rid)
            to_create.append(row)
    return {"to_create": to_create, "skipped": skipped}
