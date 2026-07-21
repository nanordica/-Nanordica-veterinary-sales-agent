"""Manual live smoke test for the calendar capability. Run AFTER granting
Calendars.Read / Calendars.ReadWrite (admin consent) in Azure:

    cd mcp && python -m scripts.smoke_calendar            # read-only: tomorrow's slots
    python -m scripts.smoke_calendar --book \
        --start 2026-07-22T09:00:00Z --end 2026-07-22T09:20:00Z \
        --attendee you@example.com --subject "Smoke test"  # creates a REAL event

Reads GRAPH_* env vars (source mcp/.env first). Never books without --book.
Organizer model: free slots are GRAPH_CALENDAR_USER's availability; a --book
run creates the event on GRAPH_SENDER's calendar, inviting both
GRAPH_CALENDAR_USER and --attendee.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from lib import graph_client as gc


def main() -> int:
    p = argparse.ArgumentParser(description="Live Graph calendar smoke test")
    p.add_argument("--duration", type=int, default=20, help="slot minutes")
    p.add_argument("--book", action="store_true",
                   help="actually create an event (requires the args below)")
    p.add_argument("--start", help="ISO UTC start, e.g. 2026-07-22T09:00:00Z")
    p.add_argument("--end", help="ISO UTC end")
    p.add_argument("--attendee", help="attendee email")
    p.add_argument("--subject", default="Ravimus smoke test")
    p.add_argument("--body", default="Smoke test — feel free to decline.")
    args = p.parse_args()

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()
    date_from = f"{tomorrow}T00:00:00Z"
    date_to = f"{tomorrow}T23:59:59Z"
    print(f"get_free_slots({date_from}, {date_to}, {args.duration}min):")
    out = gc.get_free_slots(date_from, date_to, args.duration)
    print(json.dumps(out, indent=2))
    if "error" in out:
        return 1

    if not args.book:
        print("\n(read-only run; pass --book --start --end --attendee to book)")
        return 0
    if not (args.start and args.end and args.attendee):
        print("--book requires --start, --end and --attendee", file=sys.stderr)
        return 2
    print(f"\nbook_slot({args.start} .. {args.end} -> {args.attendee}):")
    res = gc.book_slot(args.start, args.end, args.attendee,
                       args.subject, args.body)
    print(json.dumps(res, indent=2))
    return 0 if res.get("booked") else 1


if __name__ == "__main__":
    sys.exit(main())
