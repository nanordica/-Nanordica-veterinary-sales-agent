from lib.discovery_plan import is_valid_email, plan_discovery


def _row(rid, email):
    return {"registry_id": rid, "first_name": "A", "last_name": "B", "email": email}


def test_email_validation():
    assert is_valid_email("a.b@example.lv")
    assert not is_valid_email("")
    assert not is_valid_email("nav e-pasta")
    assert not is_valid_email("a@b")          # no dot in domain
    assert not is_valid_email("a b@c.lv")     # whitespace


def test_plan_filters_and_counts():
    rows = [_row("V-1", "a@b.lv"), _row("V-2", ""), _row("V-3", "bad"),
            _row("V-4", "d@e.lv"), _row("V-5", "f@g.lv")]
    plan = plan_discovery(rows, existing_ids={"V-4"})
    assert [r["registry_id"] for r in plan["to_create"]] == ["V-1", "V-5"]
    assert plan["skipped"] == {"existing": 1, "no_email": 1, "bad_email": 1}


def test_duplicate_registry_id_within_csv_skipped():
    rows = [_row("V-1", "a@b.lv"), _row("V-1", "x@y.lv")]
    plan = plan_discovery(rows, existing_ids=set())
    assert len(plan["to_create"]) == 1
    assert plan["skipped"]["existing"] == 1


def test_expired_certificates_are_still_included():
    rows = [{**_row("V-1", "a@b.lv"), "valid_until": "2020-01-01"}]
    plan = plan_discovery(rows, existing_ids=set())
    assert len(plan["to_create"]) == 1
