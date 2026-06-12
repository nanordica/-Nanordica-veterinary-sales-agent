"""Create a Pipedrive person + deal (stage Discovered) for every new
e-mail-bearing registry row. Dedup by registry_id against ALL existing deals
(including Lost: opted-out vets are never re-created).

Usage:
    cd mcp && python -m scripts.discovery          # DRY_RUN=1 by default
    DRY_RUN=0 python -m scripts.discovery          # live

Re-running is idempotent: existing registry_ids are skipped.
Writes a summary to logs/discovery-YYYY-MM-DD.log.
"""
import os
import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import pipedrive_client as pc
from lib import deal_state
from lib.discovery_plan import plan_discovery
from lib.dryrun import is_dry_run, dry_log
from lib.field_map import resolve_stage_id
from lib.registry_merge import read_registry_csv


def _existing_registry_ids(dry: bool) -> set[str]:
    """registry_id of every non-deleted deal (any stage/status)."""
    ids: set[str] = set()
    start = 0
    while True:
        res = pc.get("deals", {"start": start, "limit": 500,
                               "status": "all_not_deleted"})
        if res.get("error"):
            if dry:
                print(f"WARNING: cannot list deals ({res['error']}); "
                      "assuming none exist (DRY_RUN)")
                return ids
            raise SystemExit(f"ERROR: cannot list deals: {res['error']}")
        for deal in res.get("data") or []:
            rid = deal_state.read_state(deal).get("registry_id")
            if rid:
                ids.add(str(rid))
        pagination = (res.get("additional_data") or {}).get("pagination") or {}
        if not pagination.get("more_items_in_collection"):
            return ids
        start = pagination.get("next_start", start + 500)


def _state_for(row: dict) -> dict:
    return {
        "registry_id": row["registry_id"],
        "email": row["email"],
        "clinic": row.get("clinic", ""),
        "valid_until": row.get("valid_until", ""),
        "practice_scope": row.get("practice_scope", ""),
        "source": "lvb+pvd" if row.get("pvd_match") == "unique" else "lvb",
    }


def _create(row: dict, stage_id: int | None, dry: bool) -> bool:
    name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
    person_body = {"name": name,
                   "email": [{"value": row["email"], "primary": True}]}
    state = _state_for(row)
    if dry:
        dry_log("discovery_create", person=person_body, deal_title=name,
                stage="Discovered", state=state)
        return True
    pres = pc.post("persons", person_body)
    person_id = (pres.get("data") or {}).get("id")
    if person_id is None:
        print(f"  FAIL person {row['registry_id']}: {pres.get('error', pres)}")
        return False
    body = {"person_id": person_id, "title": name, "stage_id": stage_id}
    body.update(deal_state.encode_state(state))
    dres = pc.post("deals", body)
    if (dres.get("data") or {}).get("id") is None:
        print(f"  FAIL deal {row['registry_id']}: {dres.get('error', dres)}")
        return False
    return True


def main() -> int:
    dry = is_dry_run()
    csv_path = Path(os.getenv("CACHE_DIR", "./cache")) / "registry.csv"
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found; run scripts.registry first")
        return 1
    rows = read_registry_csv(csv_path)

    stage_id = resolve_stage_id("Discovered")
    if stage_id is None and not dry:
        print("ERROR: stage 'Discovered' unknown; run scripts.pipedrive_setup first")
        return 1

    existing = _existing_registry_ids(dry)
    plan = plan_discovery(rows, existing)
    created = failed = 0
    for row in plan["to_create"]:
        if _create(row, stage_id, dry):
            created += 1
        else:
            failed += 1

    skipped = plan["skipped"]
    summary = (f"DRY_RUN={dry} registry_rows={len(rows)} "
               f"existing_in_pipedrive={len(existing)} created={created} "
               f"failed={failed} skipped_existing={skipped['existing']} "
               f"no_email={skipped['no_email']} bad_email={skipped['bad_email']}")
    print(summary)

    logs = Path(os.getenv("LOGS_DIR", "./logs"))
    logs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    with (logs / f"discovery-{stamp}.log").open("a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {summary}\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
