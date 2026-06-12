from lib import setup_plan
from lib.constants import STAGES, CUSTOM_FIELDS


def test_plan_creates_everything_when_empty():
    plan = setup_plan.plan_setup(
        existing_pipelines=[], existing_stages=[], existing_fields=[])
    assert plan["create_pipeline"] is True
    assert [s["name"] for s in plan["create_stages"]] == STAGES
    assert {f["name"] for f in plan["create_fields"]} == {n for n, _ in CUSTOM_FIELDS}


def test_plan_idempotent_when_all_present():
    pipelines = [{"id": 5, "name": "ravimus-latvia-vets"}]
    stages = [{"name": n, "id": i + 1, "pipeline_id": 5} for i, n in enumerate(STAGES)]
    fields = [{"name": n, "key": f"k_{n}"} for n, _ in CUSTOM_FIELDS]
    plan = setup_plan.plan_setup(pipelines, stages, fields)
    assert plan["create_pipeline"] is False
    assert plan["pipeline_id"] == 5
    assert plan["create_stages"] == []
    assert plan["create_fields"] == []


def test_plan_adds_only_missing_stage():
    pipelines = [{"id": 5, "name": "ravimus-latvia-vets"}]
    stages = [{"name": n, "id": i + 1, "pipeline_id": 5}
              for i, n in enumerate(STAGES) if n != "Lost"]
    fields = [{"name": n, "key": f"k_{n}"} for n, _ in CUSTOM_FIELDS]
    plan = setup_plan.plan_setup(pipelines, stages, fields)
    assert [s["name"] for s in plan["create_stages"]] == ["Lost"]


def test_plan_ignores_same_named_stages_in_other_pipelines():
    # Our pipeline does not exist yet, but another pipeline already has a
    # stage named "Qualified". The planner must still create ALL 8 stages.
    pipelines = [{"id": 9, "name": "some-other-pipeline"}]
    stages = [{"name": "Qualified", "id": 99, "pipeline_id": 9}]
    plan = setup_plan.plan_setup(pipelines, stages, [])
    assert plan["create_pipeline"] is True
    assert [s["name"] for s in plan["create_stages"]] == STAGES
