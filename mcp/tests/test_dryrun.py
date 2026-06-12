from lib import dryrun


def test_dry_run_on_by_default(monkeypatch):
    monkeypatch.delenv("DRY_RUN", raising=False)
    assert dryrun.is_dry_run() is True


def test_dry_run_off_when_zero(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "0")
    assert dryrun.is_dry_run() is False


def test_dry_run_on_when_one(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    assert dryrun.is_dry_run() is True


def test_dry_log_returns_marker():
    out = dryrun.dry_log("send_mail", to="a@b.c", subject="x")
    assert out["dry_run"] is True
    assert out["action"] == "send_mail"
    assert out["details"]["to"] == "a@b.c"
