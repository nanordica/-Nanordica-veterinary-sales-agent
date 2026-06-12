"""Provision the Ravimus pipeline idempotently, then persist the field/stage map.

Usage:
    cd mcp && python -m scripts.pipedrive_setup        # honours DRY_RUN
Run twice live: the second run must create nothing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import pipedrive_client as pc
from lib.constants import PIPELINE_NAME, STAGES
from lib.setup_plan import plan_setup
from lib.field_map import save_field_map
from lib.dryrun import is_dry_run


def _fetch_state():
    pipelines = pc.get("pipelines").get("data") or []
    stages = pc.get("stages", {"limit": 500}).get("data") or []
    fields = pc.get("dealFields", {"limit": 500}).get("data") or []
    return pipelines, stages, fields


def main() -> int:
    dry = is_dry_run()
    pipelines, stages, fields = _fetch_state()
    plan = plan_setup(pipelines, stages, fields)
    print(f"DRY_RUN={dry} plan: pipeline={plan['create_pipeline']} "
          f"stages={[s['name'] for s in plan['create_stages']]} "
          f"fields={[f['name'] for f in plan['create_fields']]}")

    pipeline_id = plan["pipeline_id"]
    if plan["create_pipeline"]:
        if dry:
            print(f"[dry] create pipeline {PIPELINE_NAME}")
        else:
            res = pc.post("pipelines", {"name": PIPELINE_NAME})
            pipeline_id = res.get("data", {}).get("id")
            print(f"created pipeline id={pipeline_id}")

    for s in plan["create_stages"]:
        if dry:
            print(f"[dry] create stage {s['name']}")
        elif pipeline_id is not None:
            pc.post("stages", {"name": s["name"], "pipeline_id": pipeline_id,
                               "order_nr": s["order_nr"]})
            print(f"created stage {s['name']}")

    for f in plan["create_fields"]:
        if dry:
            print(f"[dry] create field {f['name']} ({f['field_type']})")
        else:
            pc.post("dealFields", {"name": f["name"], "field_type": f["field_type"]})
            print(f"created field {f['name']}")

    if dry:
        print("[dry] skipping field-map write")
        return 0

    # Re-fetch to capture ids/keys for everything (created + pre-existing).
    pipelines, stages, fields = _fetch_state()
    pipeline_id = next((p["id"] for p in pipelines if p["name"] == PIPELINE_NAME), None)
    stage_ids = {s["name"]: s["id"] for s in stages
                 if s.get("pipeline_id") == pipeline_id and s["name"] in STAGES}
    # Match created custom fields by name -> hashed key.
    from lib.constants import CUSTOM_FIELDS
    wanted = {n for n, _ in CUSTOM_FIELDS}
    field_keys = {f["name"]: f["key"] for f in fields if f["name"] in wanted}
    save_field_map({"pipeline_id": pipeline_id, "stage_ids": stage_ids,
                    "field_keys": field_keys})
    print(f"wrote field map: pipeline={pipeline_id} "
          f"stages={len(stage_ids)} fields={len(field_keys)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
