"""Tool-level tests that don't hit the network (early-return branches)."""
from tools.pipedrive_deals import pipedrive_list_deals, pipedrive_create_deal


def test_list_deals_unknown_stage_name(monkeypatch, tmp_path):
    # Empty field map -> stage name cannot resolve -> early error, no HTTP call.
    monkeypatch.setenv("FIELD_MAP_PATH", str(tmp_path / "none.json"))
    out = pipedrive_list_deals.fn(stage="Nonexistent")
    assert "error" in out and "unknown stage" in out["error"]


def test_create_deal_unknown_stage_name(monkeypatch, tmp_path):
    monkeypatch.setenv("FIELD_MAP_PATH", str(tmp_path / "none.json"))
    out = pipedrive_create_deal.fn(1, "Test", "Nonexistent")
    assert "error" in out and "unknown stage" in out["error"]
