# Review findings — email-rajad ja näidiskirjad

*2026-07-27. Three-way parallel review of the v1 funnel/copy note: (1) repo/design consistency, (2) cold-email craft vs email-marketing-bible + `lv-vet-email-funnel` references, (3) Latvian language QA per `latvian-qa.md`. Findings deduplicated and ranked.*

***2026-07-28 pruning:** the v1 note was superseded by [email-lehter-v2.md](email-lehter-v2.md); structural A-block findings 1–5 were resolved by the v2 redesign and are collapsed below. Everything else (medical claims, compliance, copy craft, Latvian language) still applies to the v1 LV letter drafts, which must be re-adapted to the v2 structure — treat this file as the checklist for that rewrite (v2 open question #5). Delete this file once K1–K10 copies are rewritten and language-checked.*

---

## A. Blockers — ~~1–5 resolved by the v2 redesign~~ + medical claims (still open)

~~1–5: phantom agents / Cal.com / wrong click mechanism / A/B split point / unimplementable path B~~ — **lahendatud v2-s (28.07):** roles fixed to real agents+tools, organizer-model calendar, clickEvents mechanism, physical Omniva dispatch made authoritative and implemented (`omniva_mail_dispatch.py` + state keys in v2 doc). A/B split remains as v2 open question #3.

6. **Medical-device claims exceed evidenced form** (product-ravimus-vet.md is the only allowed source):
   - E1 "dziedēja brūces gandrīz divreiz ātrāk nekā sudraba pārsēji" — RCT was **human DFU patients** (n=30), metric = wound-area reduction; "Nedrīkst teikt" forbids implying an animal study. Required framing: "pētījumā ar cilvēku pacientiem (identiska tehnoloģija) brūču laukums samazinājās ~2× ātrāk". Same defect in "Rakendatud reeglid".
   - Tänukiri dressing-change tip ("kad eksudāts sasniedz malu") — no source in any product file; remove or replace with a sourced fact.
   - E-FU3 "ilgi nedzija ar ierastajiem pārsējiem" — over-claims; evidenced form: "24 dienas nedzija" (no claim about which dressings failed).
   - E-FU3's pointer `equine-wound-care-case-study.md` is outside outreach-writer's allowed sources (lives only in `Ravimus tooteinfo/`); point to product-ravimus-vet.md §4 or copy the case into skill references + widen the agent rule.
   - Verified OK: S. aureus in-vitro claim; sample sizes 5×5 / 8×9 / 10×10 cm.

## B. Compliance & incentive architecture

7. **Opt-out line missing from FU1–FU3 and breakup** — the doc's own summary claims every email carries one; only E1 and E2-B do. Add the reference wording to every send: *"Ja nevēlaties no manis vairāk saņemt vēstules, dodiet ziņu, atbildot uz šo e-pastu."* Standardize E1/E2-B onto the same line (E2-B's current one is also ungrammatical — see D).
8. **One discount scheme, stated once.** Current state: FU2 −10%, E6-B −15%, design doc knows only −10%, variant B = 100% sample coupon. The 0→−10→−15 escalation trains prospects to wait and rewards silence over engagement (early "kods" chooser gets −10%, ignorer gets −15%). Fix: single depth (−10% per design, or amend design), code appears exactly once (E6-B); FU2 becomes sample-only (*"Atbildiet «paraugs», un tas ir ceļā."*) — which also frees the code as a fresh 6th angle if ever needed.
9. **E1 "esmakiri + BCC"** — `mail_send` has no BCC; audit trail = Pipedrive note + `emails_sent`/`last_contact_at`. Fix wording.
10. **Data-source disclosure** (latvia-market.md): add once to E1: *"Jūsu kontaktu atradām publiskajā veterinārārstu reģistrā."*

## C. Copy craft

11. **CTA doctrine conflict — needs an explicit decision.** `cold-outreach.md` mandates imperative CTAs; email-marketing-bible §14 endorses soft interest-CTAs; the doc follows the bible while claiming both. Recommended middle path: interest-based content, imperative sentence (FU3: *"Atbildiet «jā», un atsūtīšu pilnu gadījumu ar attēliem."*). Record the decision in cold-outreach.md or the funnel doc.
12. **E1 personalization runs on the weakest tier.** Add an `{avarida_fakts}` tier-1 opening slot (per personalization.md hierarchy) as sentence 1; move `{tīkls_fakts}` from E2-A (warmest email) to E1 (coldest); E2-A leans on the engagement itself. Also E1's link needs an action verb (*"Apskatiet gadījumu šeit: {UTM_saite}"*) and the competing "Ja noder, pastāstīšu vairāk" reply-CTA cut.
13. **FU3 must branch on `{dzīvnieki}`.** Horse case to a small-animal list is the mis-personalization personalization.md exists to prevent. Equine case for equine vets; cat/dog case or atraumatic-change angle for small-animal. Only the horse case exists → content gap to log.
14. **Subjects:** zero personalization tokens (project spec wants clinic/species; only E2-B complies). E6-B "−15% jūsu kabinetam" is a promotions-tab trigger — reframe (*"jūsu personīgais kods nākamajam gadījumam"*). Breakup "aizveru šo pavedienu" is the most template-recognizable breakup formula → *"pēdējā vēstule no manis"*. Provide a B-subject for E1 (subject = primary A/B axis per ab-testing.md).
15. **Ladder details:** FU1–breakup all under the claimed 50-word floor (FU2 ≈ 35 words, generic, weakest email — one species clause fixes it). No link anywhere in FU1–breakup → click-exit from the ladder only exists on day 0; re-include `{UTM_saite}` once (FU3 = the natural spot). No preheader text defined (define per email, front-load evidence). No send-time snapping ("saatmine nihkub järgmisele T–N hommikule", per ab-testing.md). No reply-SLA in Vastuste käsitlus (add: same working day). Thank-you email: add referral line (*"Ja kolēģim tas noderētu, ar prieku nosūtīšu paraugu arī viņam."*).
16. **No re-engagement after Lost.** Add a dormant path: Lost `no-reply` gets one new-evidence email at +60–90 p (new case/publication), distinct from the ladder.
17. **utm_content slugs unassigned.** funnel-framework.md mandates `utm_content=<kirja-nurk>-<utm_id>` + `ravimusvet-` campaign prefix; add a slug column to the ladder table (esmakiri-a, fu3-gadijums, e2a-akademija, …) — otherwise E1 vs E2-A clicks are indistinguishable.

## D. Latvian language (full table in review transcript; priorities for language-checker + native pass)

18. **CERTAIN grammar fixes** (apply before any send):
    - `lai izmēģināt` → `lai izmēģinātu` (E2-B); `Atbildiet «atrakstīties» atteikties` → `Atbildiet ar «atrakstīties», lai atteiktos…` (E2-B)
    - `kā turējās pārsēja maiņa` → `kā veicās pārsēja maiņa` (E5-B)
    - Semantic inversions where the EE paraphrase is right and the LV is wrong (claim-adjacent!): E-FU1 `brūce nelīp` → `pārsējs nelīp pie brūces`; E5-B `Ja der jūsu gadījumam akadēmijā` → `Ja jūsu gadījums der akadēmijai`; tänukiri `satur mitrumu` → `uztur mitru vidi`.
    - `uzaicinājums akadēmijai` → `uzaicinājums uz akadēmiju` (E2-A subject); `ar mūsu Meelis` → name must decline (native to confirm form); `Kad izmēģināt` → `Kad būsiet izmēģinājuši` (E4-B); `arī ja` → `arī tad, ja`; `Tā saruna būs konkrēta` → `Tad saruna būs konkrētāka` (E3-A); `lūk personīgs kods` → `lūk, personīgs kods` (E6-B); FU3 relative clause: `Zirgam bija hroniska distālās ekstremitātes brūce, kas … ilgi nedzija`.
    - Systemic: drop English-style comma before clause-joining `un` (E-FU1, breakup, E2-B, E5-B, E6-B); present tense where future/subjunctive is needed (`Atsūtu` → `Nosūtīšu`; `kas testē` → `kas testētu`).
19. **Token declension is a template-design bug.** `{dzīvnieki}` never works in nominative (5 slots need gen./instr.); `{kliinika}` needs dat./acc. in 3 slots; `{pakomāts}` needs acc. Fix: per-slot case tags (`{dzīvnieki:gen}`) with declined forms in contact data, or rephrase so nominative works (colon pattern: `…uz Omniva pakomātu: {pakomāts}`; possessive: `jūsu klīnikā`). `{laiks}` needs a documented date-time format; `{tīkls_fakts}` needs a defined leading separator (currently glued to "acīs").
20. **Gender.** `pamēģiniet pats` / `jūsu paša` break for female vets (degender: `savā praksē` / `jūsu pašu prakse`); `{uzvārds}` is gendered in Latvian (Bērziņš/Bērziņa) — pipeline must deliver the correct form; native decides vocative in salutations.
21. **FNR (native judgment):** `īsi` → `īsumā`; `sīkstas` → `grūti dzīstošas`; `darbagalds` → `jūsu pašu prakse`; `Ravimus VET laboratorijā uzrādīja` is ambiguous (reads "in the Ravimus VET lab") → `Laboratorijas testos Ravimus VET uzrādīja`; `Super!` → `Lieliski!`; `kabinets` → `prakse`; «» vs „" — pick one convention; capitalize `Jūs/Jūsu`? — one decision, applied everywhere. Terminology otherwise verified correct (pārsējs, granulācija, eksudāts, pakomāts = Omniva's own term, "Brūču aprūpes akadēmija" natural).

## E. Fixes outside the funnel doc

22. **`references/email-templates-lv.md` is stale vs canonical design:** prescribes open-ended sequence with waits 3/4/7/10/14/21–30; design + tick + outreach-writer implement fixed 5 × 3/5/8/13 with `emails_sent >= 5` guardrail. Fix the reference (the funnel doc's ladder is correct).
23. **Sender persona:** doc signs "Meelis" (ravimus@), skill template signs "Karmen" — one persona, everywhere. Also consider real-person mailbox vs role-box per deliverability.md.
24. **Orchestration TODO** (already on roadmap): wire calendar_* + omniva_* into `/tick` and outreach-writer; without it E3-A/E4-B steps have no executor.

---

## Top priorities

1. **A-block items 4+5** — decide the A/B split point and the authoritative sample-fulfilment model; everything in path B hangs on this.
2. **A-block item 6 + D semantic inversions** — medical-claims compliance; these are the only findings that could cause real-world harm if the emails ship.
3. **B7 opt-out lines** — the one outright legal-compliance gap; four-line fix.
4. **D19 token declension scheme** — template-design decision that touches every email; cheapest to fix before copy iterations continue.
5. **A1–A3 phantom agents/mechanisms** — quick wording fixes that stop the doc from misleading the next implementer.
