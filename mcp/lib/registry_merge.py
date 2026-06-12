"""Join LVB rows (primary, has e-mails) with PVD records (clinic/address) by
exact normalized full name; unique match or nothing (spec decision 3).
Reads/writes cache/registry.csv with a fixed column order."""
import csv
from pathlib import Path

REGISTRY_COLUMNS = ["registry_id", "first_name", "last_name", "email",
                    "valid_until", "practice_scope", "clinic", "address",
                    "pvd_match"]


def normalize_name(name: str) -> str:
    """Lowercase, collapse whitespace. Diacritics preserved."""
    return " ".join(name.split()).lower()


def merge_registries(lvb_rows: list[dict], pvd_records: list[dict]) -> list[dict]:
    by_name: dict[str, list[dict]] = {}
    for rec in pvd_records:
        by_name.setdefault(normalize_name(rec["name"]), []).append(rec)
    out = []
    for vet in lvb_rows:
        key = normalize_name(f"{vet['first_name']} {vet['last_name']}")
        matches = by_name.get(key, [])
        row = {**vet, "clinic": "", "address": "",
               "pvd_match": "none" if not matches else "ambiguous"}
        if len(matches) == 1:
            row.update(clinic=matches[0]["clinic"], address=matches[0]["address"],
                       pvd_match="unique")
        out.append({k: row.get(k, "") for k in REGISTRY_COLUMNS})
    return out


def write_registry_csv(rows: list[dict], path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_registry_csv(path) -> list[dict]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]
