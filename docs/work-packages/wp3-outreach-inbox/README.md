# wp3: kirjade saatmine ja vastuvõtt

**Omanik:** Annelis Rum (Communication Manager)
**Disaini sammud:** 3, 4 ([ehitusjärjekord](../../ravimus-lead-pipeline-design.md#ehitusjärjekord))

## Missioon

Ehita kogu kirjavahetuse pool: mail-mcp saatmiskaitseraudadega,
outreach-writer, mis kirjutab personaliseeritud lätikeelseid kirju,
keelekontroll ja inbox-triage, mis vastused klassifitseerib. Kirja toon,
A/B sõnastus ja vastuste tõlgendamine on sinu kui kommunikatsioonijuhi
otsustada; [lv-vet-email-funnel](../../../.claude/skills/lv-vet-email-funnel/SKILL.md)
skill annab mallid ja läti keele praktikad ette.

## Tulemid

- [ ] `mcp/mail-mcp/` (MS Graph): `send_mail` ja `list_new_messages`;
      server ise jõustab piirid: ≤1 kiri lead'ile 24 h, max 5 kirja,
      opt-out blokeerimisnimekiri, DRY_RUN
      ([tööriistakiht](../../ravimus-lead-pipeline-design.md#tööriistakiht--kohalikud-mcp-serverid))
- [ ] `.claude/agents/outreach-writer.md`: staadiumiteadlik, läti keeles,
      A/B esmakiri (A: personaalne link, B: näidise sooduskood), redel
      3/5/8/13 päeva, iga kiri uue sisuga, loobumisrida igas kirjas;
      faktid ainult skilli `product-ravimus-vet.md`-st ja Wixi tootelehelt
      ([outreach-writer](../../ravimus-lead-pipeline-design.md#outreach-writer))
- [ ] Keelekontrolli-subagent: läti keele toon, viisakusvormid,
      arusaadavus; jookseb enne iga saatmist, tugi skilli
      [latvian-qa.md](../../../.claude/skills/lv-vet-email-funnel/references/latvian-qa.md)
- [ ] `.claude/agents/inbox-triage.md`: Graphi delta-lugemine, saatja
      sidumine deal'iga, klassifikatsioon (huvi / "ei" / opt-out / bounce /
      out-of-office), tundmatu saatja → note üldlogisse
      ([inbox-triage](../../ravimus-lead-pipeline-design.md#inbox-triage))

## Sõltuvused

DRY_RUN-is saad kirju koostada ja hinnata ilma ühegi võtmeta, alusta
sellest. Deal'i field'idest personaliseerimine vajab wp1 `pipedrive-mcp`-d;
päris saatmine vajab MS Graphi tokeneid (Mardilt, kui jõuab). Triage'i
klassifikatsioonipiirid pane paika koos Meelisega, sest Lost-põhjused
elavad tema pipeline'is.

## Valmis, kui

1. Outreach-writer koostab DRY_RUN-is mõlema A/B haru esmakirja, mis
   läbib keelekontrolli ja milles iga fakt on jälgitav lubatud allikani.
2. mail-mcp keeldub teisest kirjast samale lead'ile 24 h sees ka siis,
   kui agent seda küsib.
3. Inbox-triage klassifitseerib testvastused (huvi, "ei", opt-out,
   out-of-office) õigesse harru.
