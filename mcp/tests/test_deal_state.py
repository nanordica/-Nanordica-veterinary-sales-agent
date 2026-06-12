import json
from lib import deal_state, field_map


def _setup_map(tmp_path, monkeypatch, key="hash_state"):
    p = tmp_path / "field_keys.json"
    monkeypatch.setenv("FIELD_MAP_PATH", str(p))
    field_map.save_field_map({"pipeline_id": 1, "stage_ids": {},
                              "field_keys": {"ravimus_hackathon_data": key}})


def test_read_state_parses_json(tmp_path, monkeypatch):
    _setup_map(tmp_path, monkeypatch)
    deal = {"hash_state": json.dumps({"score": 80, "email": "v@c.lv"})}
    assert deal_state.read_state(deal) == {"score": 80, "email": "v@c.lv"}


def test_read_state_empty_when_blank(tmp_path, monkeypatch):
    _setup_map(tmp_path, monkeypatch)
    assert deal_state.read_state({"hash_state": ""}) == {}
    assert deal_state.read_state({}) == {}


def test_read_state_empty_on_bad_json(tmp_path, monkeypatch):
    _setup_map(tmp_path, monkeypatch)
    assert deal_state.read_state({"hash_state": "not json"}) == {}


def test_encode_state_roundtrips(tmp_path, monkeypatch):
    _setup_map(tmp_path, monkeypatch)
    body = deal_state.encode_state({"score": 80})
    assert body == {"hash_state": json.dumps({"score": 80}, ensure_ascii=False)}


def test_encode_state_empty_when_no_key(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELD_MAP_PATH", str(tmp_path / "missing.json"))
    assert deal_state.encode_state({"score": 80}) == {}
