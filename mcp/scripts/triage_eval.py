"""Eval harness for parcel_triage: run the whole inbox through one or more
models and score them.

Triage is a small, well-specified task (classify + extract), so the cheapest
model that scores clean is the right one to run in cron. This script makes
that call measurable instead of assumed.

Ground truth lives in CASES below, keyed by a subject fragment; add a line
when a new kind of mail shows up. Scoring:
  - classification: is_shipping_request vs expected
  - fields: name / phone / machine compared loosely (case-insensitive
    substring, digits-only for phones) — only for shipping requests
  - latency per message

Usage (from mcp/):
    python -m scripts.triage_eval --models haiku,sonnet,opus --top 20
    python -m scripts.triage_eval --models haiku --top 20 --verbose
"""
import argparse
import json
import re
import subprocess
import time

from scripts import parcel_triage as pt
from scripts.omniva_mail_dispatch import list_recent_inbox, strip_html

# subject fragment -> (is_shipping, name, phone, place-fragment)
# NB the model sees ONE mail at a time, so a follow-up in a thread legitimately
# carries only the field it adds — those rows list the earlier fields as None.
# The place fragment is matched against machine OR address: naming a town
# ("Viljandisse Männimäele") instead of a machine is correct extraction; the
# code resolves it against Omniva's feed.
CASES = [
    # Most specific fragments first — a "Re:" follow-up only carries what it
    # adds, so its row lists the earlier fields as None.
    ("Re: Meelis vajab haavasidemeid", True, "Meelis Kadaja", None, "Rebase"),
    ("Meelis vajab haavasidemeid", True, "Meelis Kadaja", "5184872", "Rebase"),
    ("Täpsustus vajalik", True, None, None, "Selver"),
    ("Paki saatmine", True, "Karl Heinla", "56281454", "Kärla"),
    ("soovin saata paki", True, "Anette Eylandt", "51902483", "Männimäe"),
    # A vet asking for a sample IS a dispatch request ("saņemt paraugu
    # testēšanai") — both models were right and the first label here was
    # wrong. Production never sees it: external senders are gated out before
    # triage, and a colleague forwarding it internally is the Vera->Karl case.
    ("ātrāka brūču dzīšana", True, None, None, None),
    ("Papildu informācija", False, None, None, None),   # "not interested"
    ("bezmaksas RavimusVET paraugs", False, None, None, None),  # asks for info
    ("Koosolek", False, None, None, None),
    ("Accepted:", False, None, None, None),
    ("Aktsepteeritud:", False, None, None, None),
    ("Investor Lounge", False, None, None, None),
    ("Manuse test", False, None, None, None),
    ("Veterinary - Flex", False, None, None, None),
]


def expected_for(subject: str):
    s = (subject or "").lower()
    for frag, ship, name, phone, machine in CASES:
        if frag.lower() in s:
            return {"ship": ship, "name": name, "phone": phone,
                    "machine": machine}
    return None


def _match(expected: str | None, got: str | None, digits: bool = False) -> bool:
    if expected is None:
        return True
    if not got:
        return False
    if digits:
        return re.sub(r"\D", "", expected) in re.sub(r"\D", "", got)
    return expected.lower() in got.lower()


def runner_for(model: str):
    """claude -p with an explicit --model; returns stdout."""
    def run(prompt: str) -> str:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", model,
             "--dangerously-skip-permissions"],
            capture_output=True, text=True, timeout=pt.CLAUDE_TIMEOUT_S)
        return res.stdout
    return run


def evaluate(model: str, messages: list, verbose: bool = False) -> dict:
    ok_class = ok_fields = graded = 0
    errors, times = [], []
    for m in messages:
        subject = m.get("subject") or ""
        exp = expected_for(subject)
        if exp is None:
            continue
        graded += 1
        sender = ((m.get("from") or {}).get("emailAddress") or {}).get("address", "")
        raw = (m.get("body") or {}).get("content", "") or m.get("bodyPreview", "")
        body = strip_html(raw) if "<" in raw else raw
        t0 = time.time()
        r = pt.triage(sender, subject, body, runner=runner_for(model))
        times.append(time.time() - t0)
        if not r.get("ok"):
            errors.append(f"{subject[:35]}: {r.get('error')}")
            continue
        cls_ok = r["is_shipping_request"] == exp["ship"]
        ok_class += cls_ok
        f = r.get("fields", {})
        if exp["ship"]:
            place = f"{f.get('machine') or ''} {f.get('address') or ''}"
            fld_ok = (_match(exp["name"], f.get("name"))
                      and _match(exp["phone"], f.get("phone"), digits=True)
                      and _match(exp["machine"], place))
            ok_fields += fld_ok
        else:
            fld_ok = True
            ok_fields += 1
        if verbose or not (cls_ok and fld_ok):
            flag = "OK " if cls_ok and fld_ok else "VIGA"
            print(f"  [{flag}] {subject[:40]:42s} ship={r['is_shipping_request']}"
                  f" (ootus {exp['ship']}) {f if exp['ship'] else ''}")
    return {"model": model, "graded": graded, "class_ok": ok_class,
            "fields_ok": ok_fields, "errors": errors,
            "avg_s": round(sum(times) / len(times), 1) if times else 0,
            "total_s": round(sum(times), 1)}


def main() -> int:
    p = argparse.ArgumentParser(description="Score triage models on the inbox")
    p.add_argument("--models", default="haiku,sonnet",
                   help="comma-separated model aliases for `claude --model`")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    inbox = list_recent_inbox(args.top)
    if "error" in inbox:
        print(json.dumps(inbox, ensure_ascii=False))
        return 1
    msgs = inbox["messages"]
    print(f"korpus: {len(msgs)} kirja, hinnatavaid "
          f"{sum(1 for m in msgs if expected_for(m.get('subject')))}\n")

    rows = []
    for model in [m.strip() for m in args.models.split(",") if m.strip()]:
        print(f"=== {model} ===")
        rows.append(evaluate(model, msgs, args.verbose))
        print()

    print(f"{'mudel':10s} {'klassif.':>10s} {'väljad':>10s} {'aeg/kiri':>10s} "
          f"{'kokku':>8s}  vead")
    for r in rows:
        g = r["graded"] or 1
        print(f"{r['model']:10s} {r['class_ok']}/{g:<8} {r['fields_ok']}/{g:<8} "
              f"{r['avg_s']:>9.1f}s {r['total_s']:>7.1f}s  {len(r['errors'])}")
        for e in r["errors"]:
            print(f"           ! {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
