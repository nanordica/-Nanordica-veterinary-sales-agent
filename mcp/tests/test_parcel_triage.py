"""parcel_triage: JSON contract + field normalisation. The model is injected
as a fake runner — no subprocess, no network."""
import json

from scripts import parcel_triage as pt


def runner_returning(payload, prefix="", suffix=""):
    def run(prompt):
        return prefix + json.dumps(payload, ensure_ascii=False) + suffix
    return run


SHIP = {"is_shipping_request": True, "confidence": 0.95,
        "reason": "Palub saata paki Kärla automaati",
        "name": "Karl Heinla", "phone": "56281454",
        "machine": "Kärla omniva", "address": None, "country": "ee",
        "weight": 0.5, "email": None, "contents": "2 karpi 10x10 sidemeid"}


def test_shipping_request_fields_normalised():
    r = pt.triage("vera@nanordica.com", "Paki saatmine", "…",
                  runner=runner_returning(SHIP))
    assert r["ok"] and r["is_shipping_request"]
    assert r["fields"] == {"name": "Karl Heinla", "phone": "56281454",
                           "machine": "Kärla omniva", "country": "EE",
                           "weight": "0.5"}          # nulls dropped, EE upper
    assert r["contents"] == "2 karpi 10x10 sidemeid"


def test_non_shipping_request_is_flagged():
    r = pt.triage("mart@nanordica.com", "Koosolek",
                  "Pane ruum kinni ja saada kutsed",
                  runner=runner_returning(
                      {"is_shipping_request": False, "confidence": 0.9,
                       "reason": "ruumibroneering", "name": None,
                       "phone": None, "machine": None, "address": None,
                       "country": None, "weight": None, "email": None,
                       "contents": None}))
    assert r["ok"] and r["is_shipping_request"] is False
    assert r["fields"] == {} and "ruumi" in r["reason"]


def test_json_inside_code_fence_and_prose():
    r = pt.triage("v@nanordica.com", "x", "y",
                  runner=runner_returning(SHIP, prefix="Vastus:\n```json\n",
                                          suffix="\n```\nAitäh!"))
    assert r["ok"] and r["fields"]["name"] == "Karl Heinla"


def test_unparseable_model_output_signals_fallback():
    r = pt.triage("v@nanordica.com", "x", "y", runner=lambda p: "ei tea")
    assert r["ok"] is False and "usable JSON" in r["error"]


def test_model_crash_signals_fallback():
    def boom(prompt):
        raise OSError("claude not found")
    r = pt.triage("v@nanordica.com", "x", "y", runner=boom)
    assert r["ok"] is False and "unavailable" in r["error"]


def test_placeholder_nulls_are_dropped():
    payload = dict(SHIP, name="null", phone="  ", machine=None)
    r = pt.triage("v@nanordica.com", "x", "y", runner=runner_returning(payload))
    assert "name" not in r["fields"] and "phone" not in r["fields"]


def test_prompt_carries_sender_subject_body():
    seen = {}

    def capture(prompt):
        seen["p"] = prompt
        return json.dumps(SHIP)
    pt.triage("vera@nanordica.com", "Paki saatmine", "Kärla automaati",
              runner=capture)
    assert "vera@nanordica.com" in seen["p"]
    assert "Paki saatmine" in seen["p"] and "Kärla automaati" in seen["p"]
