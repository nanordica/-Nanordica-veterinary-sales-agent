import json
from lib import field_map


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    p = tmp_path / "field_keys.json"
    monkeypatch.setenv("FIELD_MAP_PATH", str(p))
    data = {"pipeline_id": 7,
            "stage_ids": {"Discovered": 1, "Lost": 8},
            "field_keys": {"score": "abc123", "email": "def456"}}
    field_map.save_field_map(data)
    assert field_map.load_field_map() == data


def test_resolve_field_key(tmp_path, monkeypatch):
    p = tmp_path / "field_keys.json"
    monkeypatch.setenv("FIELD_MAP_PATH", str(p))
    field_map.save_field_map({"pipeline_id": 1, "stage_ids": {},
                              "field_keys": {"score": "hash_score"}})
    assert field_map.resolve_field_key("score") == "hash_score"


def test_load_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELD_MAP_PATH", str(tmp_path / "nope.json"))
    assert field_map.load_field_map() == {"pipeline_id": None, "stage_ids": {}, "field_keys": {}}
