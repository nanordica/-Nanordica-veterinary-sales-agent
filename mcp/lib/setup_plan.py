"""Pure planner: given current Pipedrive state, decide what to create.
No I/O — the script in scripts/pipedrive_setup.py performs the actions."""
from lib.constants import PIPELINE_NAME, STAGES, CUSTOM_FIELDS


def plan_setup(existing_pipelines: list, existing_stages: list,
               existing_fields: list) -> dict:
    """Return a create-plan that is idempotent against the current state.

    existing_stages/existing_fields are matched by name (case-sensitive).
    Stages are only considered if they belong to the matched pipeline_id."""
    match = next((p for p in existing_pipelines if p.get("name") == PIPELINE_NAME), None)
    pipeline_id = match["id"] if match else None

    # Only stages belonging to OUR pipeline count; if ours doesn't exist yet,
    # create all (ignore same-named stages from other pipelines).
    have_stage_names = {
        s["name"] for s in existing_stages
        if pipeline_id is not None and s.get("pipeline_id") == pipeline_id
    }
    create_stages = [
        {"name": name, "order_nr": i + 1}
        for i, name in enumerate(STAGES)
        if name not in have_stage_names
    ]

    have_field_names = {f["name"] for f in existing_fields}
    create_fields = [
        {"name": name, "field_type": ftype}
        for name, ftype in CUSTOM_FIELDS
        if name not in have_field_names
    ]

    return {
        "create_pipeline": match is None,
        "pipeline_id": pipeline_id,
        "create_stages": create_stages,
        "create_fields": create_fields,
    }
