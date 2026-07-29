"""room_booking_watch: candidate filter + registry round-trip (no network)."""
from scripts import room_booking_watch as rw


def test_room_candidate_filter():
    own = "ravimus@nanordica.com"
    assert rw.is_room_request("vera@nanordica.com", own,
                              "Ruumi broneerimine homseks", "")
    assert rw.is_room_request("mart@nanordica.com", own,
                              "", "kas saaks Investor Lounge broneerida?")
    assert not rw.is_room_request("keegi@gmail.com", own, "broneeri ruum", "")
    assert not rw.is_room_request(own, own, "ruum", "")
    assert not rw.is_room_request("vera@nanordica.com", own,
                                  "soovin saata paki", "")


def test_registry_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(rw, "STATE_PATH", tmp_path / "reg.json")
    assert rw.load_registry() == {}
    rw.save_registry({"m1": {"status": "booked"}})
    assert rw.load_registry()["m1"]["status"] == "booked"
