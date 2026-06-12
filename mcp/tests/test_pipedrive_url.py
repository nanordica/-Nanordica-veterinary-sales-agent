from lib import pipedrive_client as pc


def test_base_url_full_domain():
    assert pc._build_base("nanordica.pipedrive.com") == "https://nanordica.pipedrive.com/v1"


def test_base_url_short_domain():
    assert pc._build_base("nanordica") == "https://nanordica.pipedrive.com/v1"


def test_missing_token_errors(monkeypatch):
    monkeypatch.delenv("PIPEDRIVE_API_TOKEN", raising=False)
    monkeypatch.setenv("PIPEDRIVE_DOMAIN", "nanordica.pipedrive.com")
    out = pc.get("deals/1")
    assert "error" in out and "PIPEDRIVE_API_TOKEN" in out["error"]
