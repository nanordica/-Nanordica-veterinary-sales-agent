# wp2: profiil ja skoor

**Omanik:** Meelis Kadaja (Chief Business Officer)
**Disaini samm:** 5 ([ehitusjärjekord](../../ravimus-lead-pipeline-design.md#ehitusjärjekord))

## Missioon

Ehita agendid, mis muudavad registrikirje müügivalmis profiiliks:
enrichment otsib veti tausta kolmes mõõtmes, qualification annab skoori
0–100. Sinu teadus- ja kliinikutaust on siin põhitööriist: publikatsioonide
ja võrgustike lugemine, kliinilise konteksti hindamine ning
meditsiiniväidete kontroll on sama töö, mida teed Nanordicas iga päev.

## Tulemid

- [ ] `.claude/agents/enrichment.md`: veebiotsing kolmes mõõtmes
      (spetsialiseerumine, suhtevõrgustik allikaviidetega, otsustusstiil);
      kirjutab field'id ja liigutab deal'i → Enriched; puuduliku profiili
      korral liigub deal edasi minimaalsega
      ([enrichment](../../ravimus-lead-pipeline-design.md#enrichment))
- [ ] `.claude/agents/qualification.md`: skoor 0–100 + põhjendus note'ina;
      rubriigis kiirabikliinik kõrgeima kaaluga, siis haavaravi/kirurgia,
      väikeloomapraksis, aktiivne luba; alla läve (30) → Lost
      ([qualification](../../ravimus-lead-pipeline-design.md#qualification))
- [ ] Käsitsi valideerimine: jooksuta mõlemat 2–3 päris Läti veti peal ja
      kontrolli, et võrgustikufaktid on tõesed ja allikaga
- [ ] Meditsiiniväidete kontroll: vaata üle
      [product-ravimus-vet.md](../../../.claude/skills/lv-vet-email-funnel/references/product-ravimus-vet.md),
      ainus lubatud tootefaktide allikas outreach'is; paranda või märgi
      väited, mida tõendid ei kata

## Sõltuvused

Agendi mustandit ja käsitsi valideerimist saad teha kohe, ilma
Pipedrive'ita. Päris Discovered deal'ide peal jooksmine vajab wp1
`pipedrive-mcp`-d ja discovery jooksu (tund 2).

## Valmis, kui

1. Discovered test-deal saab enrichment'ist kolm täidetud field'i,
   võrgustikufaktid allikaviitega.
2. Qualification kirjutab skoori ja põhjenduse; kiirabikliiniku vet saab
   kõrgema skoori kui võrdne tava-vet.
3. `product-ravimus-vet.md` väited on üle vaadatud ja vajadusel parandatud.
