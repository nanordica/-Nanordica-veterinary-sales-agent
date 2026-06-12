# ISSUES

Issues found while running the pipeline end to end. Newest first. Each entry
has a severity, where it lives, what happens, and a suggested fix.

Severity: **high** = correctness/compliance, fix before real launch ·
**medium** = hurts results or operability · **low** = minor/cosmetic.

---

## Open

### 1. Opt-out detection must cover plain language — **high**

**Where:** `inbox-triage` agent (`.claude/agents/inbox-triage.md`) and any
opt-out matching in the tick.

**What happens:** During the 2026-06-12 live test a recipient replied
"i'm not interested. please don't send emails anymore." A keyword-only
matcher (`unsubscribe` / `stop` / `nevēlos`) did not recognise it, so the
opt-out was not routed to Lost. Opt-outs phrased in plain language must be
honoured: "not interested", "don't send / don't email", "no thanks",
"take me off", "leave me alone", "please remove", in LV / EN / RU.

**Fix:** Make `inbox-triage` classify intent (not keywords) and treat any
clear unwillingness to receive mail as `opt-out` → Lost. Add test cases with
plain-language phrasings, including the exact line above.

### 2. A reply from an already-advanced deal must not be dropped — **high**

**Where:** tick inbox flow / `inbox-triage`.

**What happens:** When a lead who is already past Contacted (Engaged or
later) replies again, the new message can carry an opt-out, a question, or
buying intent. If the stage-advance logic only acts on `Contacted → Engaged`,
a later reply produces no note and no action — it is silently swallowed. In
the live test this hid an opt-out for an Engaged lead.

**Fix:** `inbox-triage` should classify every new inbound message regardless
of the deal's current stage, always write a note, and route opt-outs to Lost
from any stage. A reply that does not change the stage should still surface
for review, never disappear.

### 3. The 24h send throttle also blocks replies to engaged leads — **medium**

**Where:** `mcp/lib/guardrails.py` (`MIN_HOURS_BETWEEN = 24`, `too_soon`),
applied by `mcp/tools/mail.py` `mail_send`, used by `outreach-writer` at the
`Engaged → reply` stage.

**What happens:** The 24h minimum between sends is applied to every send,
including a direct reply to a lead who just wrote in. So if a lead replies and
asks a question, the system cannot answer for up to 24h without the send being
refused `too_soon`. The throttle is meant for cold follow-ups, not for
replying to an inbound.

**Fix:** Exempt the inbound-reply path (Engaged-stage reply) from `too_soon`
while keeping the other guards (allowlist, email match, opt-out, max 5). For
example, pass a `reply_to_inbound=True` flag through `mail_send` that skips
only the throttle check.

### 4. `language-checker` subagents could not read the product reference — **medium**

**Where:** `language-checker` agent + `lv-vet-email-funnel` skill
(`references/product-ravimus-vet.md`).

**What happens:** During the test, `language-checker` subagents' file tools
returned the repo as empty, so they could not read
`references/product-ravimus-vet.md` and failed the product-claim gate (a false
FAIL) until the product facts were passed to them inline. In `/tick` this is
fail-safe (it blocks sends rather than passing unverified claims), but it would
block all outgoing mail.

**Fix:** Ensure the subagent runtime has reliable repo file access, or have
the caller pass the product facts inline to `language-checker` rather than
relying on it to open the file. Add a startup check that the reference file is
readable before the gate runs.

### 5. Wix coupon search lags creation — **low**

**Where:** `mcp/lib/wix_client.py` (`create_coupon` / `check_coupon_usage`),
relevant to `sales-detector`.

**What happens:** `check_coupon_usage` returns `found: False` for a few
seconds after `create_coupon`, even though `create_coupon` already returned the
coupon id. Wix's coupon query index is eventually consistent; create and the
order/read paths are immediate, only the search lags.

**Fix:** Do not verify a coupon by query immediately after creating it. If a
just-created coupon must be confirmed, retry the query with a short backoff, or
trust the id returned by `create_coupon`.

### 6. Test artifacts left in production — **medium (cleanup)**

The 2026-06-12 live test wrote real records that should be removed before or
during launch:

- **Pipedrive** (`ravimus-hackathon` pipeline, `source: manual-test`):
  deal 952 Annelis Rum (Engaged) and deal 953 Karmen Tigas (Lost, opt-out).
- **Wix coupons:** `RVET-LIVECHECK-1` (1%), `RVET-KARMEN-FREE` (100%),
  `RVET-ANNELIS-FREE` (100%). `wix_client` has no delete; remove from the Wix
  dashboard.
- **`mcp/.env`** has `MAIL_ALLOWLIST` set to the two test addresses (phase-2
  safety). **Clear it before real outreach** or every real send is refused
  `not_in_allowlist`.

---

## Resolved (2026-06-12)

- **STATE_KEYS missing dedup markers** — `sample_reminder_sent` and
  `thanked_at` added to `mcp/lib/constants.py` (PR #14, merged). Docs-only;
  the markers already persisted.
- **MS Graph mail not live** — app-only Mail.Send + Mail.Read granted and
  verified (real send → 202, inbox delta → 200). Closed issue #10.
- **WP1 pipedrive-mcp + lost_reason** — built and verified; `lost_reason` is a
  string field by design, `opt-out` matches the guardrail. Closed issue #8.
- **Integration runbook (keys, setup, Wix/mail live checks, discovery)** —
  all checks green. Closed issue #7.
