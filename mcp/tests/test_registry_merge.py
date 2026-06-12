from lib.registry_merge import (merge_registries, write_registry_csv,
                                read_registry_csv, REGISTRY_COLUMNS)

LVB = [
    {"registry_id": "V-1", "first_name": "Līga", "last_name": "Truntika",
     "email": "l@t.lv", "valid_until": "2027-01-01", "practice_scope": "mājas dzīvn."},
    {"registry_id": "V-2", "first_name": "Jānis", "last_name": "Ozols",
     "email": "", "valid_until": "2026-01-01", "practice_scope": "zirgi"},
    {"registry_id": "V-3", "first_name": "Anna", "last_name": "Liepa",
     "email": "a@l.lv", "valid_until": "2025-01-01", "practice_scope": ""},
]
PVD = [
    {"name": "Līga  Truntika", "clinic": "Līga-vet, SIA", "address": "Bauska",
     "practice_type": "ambulatora"},
    {"name": "Anna Liepa", "clinic": "K1", "address": "Rīga", "practice_type": "kabinets"},
    {"name": "anna liepa", "clinic": "K2", "address": "Cēsis", "practice_type": "kabinets"},
]


def test_unique_name_match_brings_clinic_and_address():
    rows = merge_registries(LVB, PVD)
    assert rows[0]["clinic"] == "Līga-vet, SIA"
    assert rows[0]["address"] == "Bauska"
    assert rows[0]["pvd_match"] == "unique"


def test_no_match_leaves_blank():
    rows = merge_registries(LVB, PVD)
    assert rows[1]["clinic"] == "" and rows[1]["pvd_match"] == "none"


def test_ambiguous_match_leaves_blank():
    rows = merge_registries(LVB, PVD)
    assert rows[2]["clinic"] == "" and rows[2]["pvd_match"] == "ambiguous"


def test_lvb_order_preserved():
    assert [r["registry_id"] for r in merge_registries(LVB, PVD)] == ["V-1", "V-2", "V-3"]


def test_csv_roundtrip_utf8(tmp_path):
    rows = merge_registries(LVB, PVD)
    path = tmp_path / "registry.csv"
    write_registry_csv(rows, path)
    back = read_registry_csv(path)
    assert back[0]["first_name"] == "Līga"
    assert list(back[0].keys()) == REGISTRY_COLUMNS
    assert len(back) == 3
