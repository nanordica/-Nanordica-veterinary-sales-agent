"""get_click_events — query the clickEvents Wix Data collection (engagement signal)."""
from lib import wix_client as w


def _patch_call(monkeypatch, response):
    """Capture the outgoing _call and return a canned response."""
    seen = {}

    def fake_call(method, path, body=None):
        seen["method"], seen["path"], seen["body"] = method, path, body
        return response

    monkeypatch.setattr(w, "_call", fake_call)
    return seen


def _wix_row(content="esmakiri-a-abc123", created="2026-07-21T09:29:28.202Z"):
    return {"id": "row-1", "dataCollectionId": "clickEvents",
            "data": {"_id": "row-1", "utmContent": content, "utmSource": "mailbox",
                     "utmMedium": "email", "utmCampaign": "ravimusvet-cold-lv",
                     "pagePath": "ravimus", "referrer": "",
                     "_createdDate": {"$date": created}}}


def test_query_targets_click_events_collection(monkeypatch):
    seen = _patch_call(monkeypatch, {"dataItems": []})
    w.get_click_events()
    assert seen["method"] == "POST"
    assert seen["path"] == "/wix-data/v2/items/query"
    assert seen["body"]["dataCollectionId"] == "clickEvents"
    assert "filter" not in seen["body"]["query"]
    assert seen["body"]["query"]["paging"]["limit"] == 100


def test_filters_by_utm_content_and_since(monkeypatch):
    seen = _patch_call(monkeypatch, {"dataItems": []})
    w.get_click_events(utm_content="esmakiri-a-abc123",
                       since="2026-07-21T00:00:00Z", limit=10)
    flt = seen["body"]["query"]["filter"]
    assert flt["utmContent"] == "esmakiri-a-abc123"
    # Wix Data compares dates only when the operand is wrapped as {"$date": ...};
    # a bare ISO string silently matches nothing (verified live 2026-07-21).
    assert flt["_createdDate"] == {"$gte": {"$date": "2026-07-21T00:00:00Z"}}
    assert seen["body"]["query"]["paging"]["limit"] == 10


def test_normalizes_rows_to_events(monkeypatch):
    _patch_call(monkeypatch, {"dataItems": [_wix_row()]})
    out = w.get_click_events()
    assert out["count"] == 1
    ev = out["events"][0]
    assert ev["utm_content"] == "esmakiri-a-abc123"
    assert ev["utm_campaign"] == "ravimusvet-cold-lv"
    assert ev["page_path"] == "ravimus"
    assert ev["clicked_at"] == "2026-07-21T09:29:28.202Z"


def test_error_passthrough(monkeypatch):
    _patch_call(monkeypatch, {"error": "Wix HTTP 403", "detail": "WDE0027"})
    out = w.get_click_events()
    assert out["error"] == "Wix HTTP 403"
