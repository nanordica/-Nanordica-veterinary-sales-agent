"""Calendar (MS Graph getSchedule + event booking) — lib and tool tests.

Only the HTTP boundary (graph_client._call) is mocked; the free-slot
computation, request shaping, lock flow, and dry-run gating are real.
"""
import fcntl

import pytest

from lib import graph_client as gc


# --- helpers ---------------------------------------------------------------

def _patch_call(monkeypatch, responses):
    """Capture outgoing _call invocations; pop canned responses in order.
    `responses` is a list (one per expected call) or a single dict reused."""
    calls = []

    def fake_call(method, path, body=None):
        calls.append({"method": method, "path": path, "body": body})
        if isinstance(responses, list):
            return responses[len(calls) - 1]
        return responses

    monkeypatch.setattr(gc, "_call", fake_call)
    return calls


def _schedule_response(items=None, working_hours=None):
    entry = {"scheduleId": "vet@nanordica.com",
             "scheduleItems": items or []}
    if working_hours is not None:
        entry["workingHours"] = working_hours
    return {"value": [entry]}


def _busy(start, end, status="busy"):
    return {"status": status,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"}}


_WH_9_17 = {"daysOfWeek": ["monday", "tuesday", "wednesday", "thursday",
                           "friday"],
            "startTime": "09:00:00.0000000",
            "endTime": "17:00:00.0000000",
            "timeZone": {"name": "UTC"}}


@pytest.fixture
def cal_env(monkeypatch):
    monkeypatch.setenv("GRAPH_CALENDAR_USER", "vet@nanordica.com")


# 2026-07-22 is a Wednesday.
DAY = "2026-07-22"


# --- get_free_slots: env + request shape -----------------------------------

def test_free_slots_env_not_set(monkeypatch):
    monkeypatch.delenv("GRAPH_CALENDAR_USER", raising=False)
    out = gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z")
    assert "error" in out and "GRAPH_CALENDAR_USER" in out["error"]


def test_free_slots_request_shape(monkeypatch, cal_env):
    calls = _patch_call(monkeypatch, _schedule_response())
    gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z",
                      duration_minutes=20)
    assert len(calls) == 1
    c = calls[0]
    assert c["method"] == "POST"
    assert c["path"] == "/users/vet%40nanordica.com/calendar/getSchedule"
    assert c["body"]["schedules"] == ["vet@nanordica.com"]
    assert c["body"]["startTime"] == {"dateTime": f"{DAY}T09:00:00Z",
                                      "timeZone": "UTC"}
    assert c["body"]["endTime"] == {"dateTime": f"{DAY}T10:00:00Z",
                                    "timeZone": "UTC"}
    assert c["body"]["availabilityViewInterval"] == 20


def test_free_slots_interval_clamped(monkeypatch, cal_env):
    calls = _patch_call(monkeypatch, _schedule_response())
    gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z",
                      duration_minutes=2)
    assert calls[0]["body"]["availabilityViewInterval"] == 5


def test_free_slots_error_passthrough(monkeypatch, cal_env):
    _patch_call(monkeypatch, {"error": "Graph HTTP 403", "detail": "x"})
    out = gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z")
    assert out["error"] == "Graph HTTP 403"


# --- get_free_slots: slot computation --------------------------------------

def test_empty_calendar_full_window_sliced(monkeypatch, cal_env):
    _patch_call(monkeypatch, _schedule_response())
    out = gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z",
                            duration_minutes=20)
    assert out["count"] == 3
    assert out["slots"][0] == {"start": f"{DAY}T09:00:00Z",
                               "end": f"{DAY}T09:20:00Z"}
    # last slot ends exactly at the window edge
    assert out["slots"][-1] == {"start": f"{DAY}T09:40:00Z",
                                "end": f"{DAY}T10:00:00Z"}


def test_busy_block_splits_window(monkeypatch, cal_env):
    _patch_call(monkeypatch, _schedule_response(
        items=[_busy(f"{DAY}T09:20:00", f"{DAY}T09:40:00")]))
    out = gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z",
                            duration_minutes=20)
    starts = [s["start"] for s in out["slots"]]
    assert starts == [f"{DAY}T09:00:00Z", f"{DAY}T09:40:00Z"]


def test_tentative_and_oof_block_free_does_not(monkeypatch, cal_env):
    _patch_call(monkeypatch, _schedule_response(items=[
        _busy(f"{DAY}T09:00:00", f"{DAY}T09:20:00", status="tentative"),
        _busy(f"{DAY}T09:20:00", f"{DAY}T09:40:00", status="oof"),
        _busy(f"{DAY}T09:40:00", f"{DAY}T10:00:00", status="free"),
    ]))
    out = gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z",
                            duration_minutes=20)
    assert [s["start"] for s in out["slots"]] == [f"{DAY}T09:40:00Z"]


def test_duration_that_does_not_fit_gap(monkeypatch, cal_env):
    # 15-minute gap between busy blocks cannot host a 20-minute slot.
    _patch_call(monkeypatch, _schedule_response(items=[
        _busy(f"{DAY}T09:00:00", f"{DAY}T09:25:00"),
        _busy(f"{DAY}T09:40:00", f"{DAY}T10:00:00"),
    ]))
    out = gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z",
                            duration_minutes=20)
    assert out["slots"] == [] and out["count"] == 0


def test_working_hours_exclude_outside_slots(monkeypatch, cal_env):
    # Window 08:00-10:00 but working hours start 09:00 -> only 09:00+ offered;
    # a slot spanning 08:40-09:00 or 08:00-08:20 must not appear.
    _patch_call(monkeypatch, _schedule_response(working_hours=_WH_9_17))
    out = gc.get_free_slots(f"{DAY}T08:00:00Z", f"{DAY}T10:00:00Z",
                            duration_minutes=30)
    starts = [s["start"] for s in out["slots"]]
    assert starts == [f"{DAY}T09:00:00Z", f"{DAY}T09:30:00Z"]


def test_working_hours_day_off_no_slots(monkeypatch, cal_env):
    # 2026-07-26 is a Sunday — not in daysOfWeek.
    _patch_call(monkeypatch, _schedule_response(working_hours=_WH_9_17))
    out = gc.get_free_slots("2026-07-26T09:00:00Z", "2026-07-26T17:00:00Z",
                            duration_minutes=20)
    assert out["count"] == 0


def test_slot_cap(monkeypatch, cal_env):
    _patch_call(monkeypatch, _schedule_response())
    out = gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T17:00:00Z",
                            duration_minutes=20, max_slots=4)
    assert out["count"] == 4 and len(out["slots"]) == 4


def test_busy_overlapping_window_edge_clipped(monkeypatch, cal_env):
    # Busy block starting before the window still blocks its overlap.
    _patch_call(monkeypatch, _schedule_response(
        items=[_busy(f"{DAY}T08:30:00", f"{DAY}T09:20:00")]))
    out = gc.get_free_slots(f"{DAY}T09:00:00Z", f"{DAY}T10:00:00Z",
                            duration_minutes=20)
    assert [s["start"] for s in out["slots"]] == [f"{DAY}T09:20:00Z",
                                                  f"{DAY}T09:40:00Z"]


# --- book_slot -------------------------------------------------------------

def _lock_env(monkeypatch, tmp_path, name="locks/cal.lock"):
    path = tmp_path / name
    monkeypatch.setenv("GRAPH_BOOK_LOCK_PATH", str(path))
    return path


def test_book_env_not_set(monkeypatch):
    monkeypatch.delenv("GRAPH_CALENDAR_USER", raising=False)
    out = gc.book_slot(f"{DAY}T09:00:00Z", f"{DAY}T09:20:00Z",
                       "lead@clinic.ee", "Ravimus demo")
    assert "error" in out and "GRAPH_CALENDAR_USER" in out["error"]


def test_book_happy_path(monkeypatch, cal_env, tmp_path):
    lock = _lock_env(monkeypatch, tmp_path)
    calls = _patch_call(monkeypatch, [_schedule_response(),
                                     {"id": "evt-123"}])
    out = gc.book_slot(f"{DAY}T09:00:00Z", f"{DAY}T09:20:00Z",
                       "lead@clinic.ee", "Ravimus demo", "Tere!")
    assert out == {"booked": True, "event_id": "evt-123",
                   "start": f"{DAY}T09:00:00Z", "end": f"{DAY}T09:20:00Z"}
    # call 1 = re-check, call 2 = create
    assert calls[0]["path"].endswith("/calendar/getSchedule")
    ev = calls[1]
    assert ev["method"] == "POST"
    assert ev["path"] == "/users/vet%40nanordica.com/events"
    body = ev["body"]
    assert body["subject"] == "Ravimus demo"
    assert body["attendees"] == [{"emailAddress":
                                  {"address": "lead@clinic.ee"},
                                  "type": "required"}]
    assert body["start"] == {"dateTime": f"{DAY}T09:00:00Z",
                             "timeZone": "UTC"}
    assert body["end"] == {"dateTime": f"{DAY}T09:20:00Z",
                           "timeZone": "UTC"}
    assert body["isOnlineMeeting"] is True
    assert body["onlineMeetingProvider"] == "teamsForBusiness"
    assert body["body"]["content"] == "Tere!"
    # lock file (in a dir that did not pre-exist) was created and released
    assert lock.exists()
    with open(lock, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)  # released -> acquirable
        fcntl.flock(f, fcntl.LOCK_UN)


def test_book_recheck_busy_no_event_created(monkeypatch, cal_env, tmp_path):
    _lock_env(monkeypatch, tmp_path)
    calls = _patch_call(monkeypatch, _schedule_response(
        items=[_busy(f"{DAY}T09:00:00", f"{DAY}T09:20:00")]))
    out = gc.book_slot(f"{DAY}T09:00:00Z", f"{DAY}T09:20:00Z",
                       "lead@clinic.ee", "Ravimus demo")
    assert out["error"] == "slot_taken"
    assert len(calls) == 1  # no POST /events issued


def test_book_recheck_error_aborts(monkeypatch, cal_env, tmp_path):
    _lock_env(monkeypatch, tmp_path)
    calls = _patch_call(monkeypatch, {"error": "Graph HTTP 500"})
    out = gc.book_slot(f"{DAY}T09:00:00Z", f"{DAY}T09:20:00Z",
                       "lead@clinic.ee", "Ravimus demo")
    assert out["error"] == "Graph HTTP 500"
    assert len(calls) == 1


# --- tools/calendar.py -----------------------------------------------------

from tools.calendar import (calendar_check_config, calendar_find_slots,
                            calendar_book_slot)


def test_calendar_check_config(monkeypatch):
    monkeypatch.setenv("GRAPH_TENANT_ID", "t")
    monkeypatch.setenv("GRAPH_CLIENT_ID", "c")
    monkeypatch.delenv("GRAPH_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("GRAPH_CALENDAR_USER", "vet@nanordica.com")
    out = calendar_check_config.fn()
    assert out == {"tenant_set": True, "client_set": True,
                   "secret_set": False, "calendar_user": "vet@nanordica.com"}


def test_find_slots_delegates(monkeypatch, cal_env):
    _patch_call(monkeypatch, _schedule_response())
    out = calendar_find_slots.fn(f"{DAY}T09:00:00Z", f"{DAY}T09:40:00Z")
    assert out["count"] == 2


def test_book_tool_dry_run_gated(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")

    def boom(*a, **k):  # any live call is a test failure
        raise AssertionError("book_slot must not be called in DRY_RUN")

    monkeypatch.setattr(gc, "book_slot", boom)
    out = calendar_book_slot.fn(42, f"{DAY}T09:00:00Z", f"{DAY}T09:20:00Z",
                                "lead@clinic.ee", "Ravimus demo")
    assert out["dry_run"] is True
    assert out["action"] == "calendar_book_slot"
    assert out["details"]["deal_id"] == 42
    assert out["details"]["attendee_email"] == "lead@clinic.ee"


def test_book_tool_live_includes_deal_id(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "0")
    monkeypatch.setattr(gc, "book_slot",
                        lambda *a, **k: {"booked": True, "event_id": "e1",
                                         "start": "s", "end": "e"})
    out = calendar_book_slot.fn(42, f"{DAY}T09:00:00Z", f"{DAY}T09:20:00Z",
                                "lead@clinic.ee", "Ravimus demo")
    assert out["booked"] is True and out["deal_id"] == 42
