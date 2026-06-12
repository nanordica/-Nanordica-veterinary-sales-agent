from datetime import datetime, timezone, timedelta
from lib import guardrails as g

NOW = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)


def _deal(email="vet@clinic.lv", last=None, sent=0, lost=None):
    return {"email": email, "last_contact_at": last,
            "emails_sent": sent, "lost_reason": lost}


def test_allows_fresh_lead():
    assert g.evaluate_send_guardrails(_deal(), "vet@clinic.lv", NOW) is None


def test_blocks_email_mismatch():
    r = g.evaluate_send_guardrails(_deal(email="a@b.c"), "other@x.y", NOW)
    assert r == "email_mismatch"


def test_blocks_optout():
    r = g.evaluate_send_guardrails(_deal(lost="opt-out"), "vet@clinic.lv", NOW)
    assert r == "opt_out"


def test_blocks_within_24h():
    last = (NOW - timedelta(hours=5)).isoformat()
    r = g.evaluate_send_guardrails(_deal(last=last), "vet@clinic.lv", NOW)
    assert r == "too_soon"


def test_allows_after_24h():
    last = (NOW - timedelta(hours=25)).isoformat()
    assert g.evaluate_send_guardrails(_deal(last=last), "vet@clinic.lv", NOW) is None


def test_blocks_at_five_sent():
    r = g.evaluate_send_guardrails(_deal(sent=5), "vet@clinic.lv", NOW)
    assert r == "max_emails"


def test_email_compare_case_insensitive():
    assert g.evaluate_send_guardrails(_deal(email="Vet@Clinic.LV"), "vet@clinic.lv", NOW) is None
