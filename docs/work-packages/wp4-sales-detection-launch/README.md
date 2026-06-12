# wp4: müügituvastus, ajastus ja lõpptest

**Omanik:** Karmen Tigas (product, partnerships)
**Disaini sammud:** 6, 8 ([ehitusjärjekord](../../ravimus-lead-pipeline-design.md#ehitusjärjekord))

## Missioon

Sulge lehtri lõpp ja vii süsteem käiku: wix-mcp näeb tellimusi ja loob
personaalseid kuponge, sales-detector seob ostud deal'idega, cron paneb
rütmi paika ning sina koordineerid mõlemat testifaasi. Tootepool on sinu
valdkond, `lv-vet-email-funnel` skill koos tootefaktidega on juba sinu
harust mestitud.

## Tulemid

- [ ] `mcp/wix-mcp/`: tellimuste loetelu, personaalse kupongi loomine
      (sh 100% näidisekupong), kupongi kasutuse kontroll; hindade muutmist
      ja tagasimakseid ei avata
      ([tööriistakiht](../../ravimus-lead-pipeline-design.md#tööriistakiht--kohalikud-mcp-serverid))
- [ ] `.claude/agents/sales-detector.md`: pollib Wixi, seob ostja e-posti
      või kupongikoodi deal'iga; päris ost → Won + tänukiri, näidise
      lunastus → Näidis tellitud + `sample_claimed_at`; seostumatu
      tellimus logitakse
      ([sales-detector](../../ravimus-lead-pipeline-design.md#sales-detector))
- [ ] Cron: tikk iga 30 min (`claude -p "/tick"`), discovery kord nädalas
- [ ] Faas 1, DRY_RUN: täisjooks päris registri peal, kirju saatmata;
      kogu tiim vaatab logid üle (kirjade kvaliteet, sihtimine, redel),
      sina koordineerid
      ([testimine](../../ravimus-lead-pipeline-design.md#testimine-ja-valmis-definitsioon))
- [ ] Faas 2, sünteetiline lead: sina oled "vet" registri CSV-s ja läbid
      kogu tee Discovered → Won (saad esmakirja, vastad küsimusega, saad
      pakkumise, ostad Wixis); deal liigub Won'i ilma inimsekkumiseta

## Sõltuvused

wix-mcp ja sales-detectori mustand ei vaja midagi peale Wixi API võtme
(Mardilt; kuni pole, DRY_RUN). Sales-detectori deal'i-sidumine vajab wp1
`pipedrive-mcp`-d. Faas 1 vajab kõiki nelja paketti, seega planeeri see
viimasesse pooltundi ja hoia tiimi ajakaval.

## Valmis, kui

1. wix-mcp loetleb tellimused ja loob 100% näidisekupongi test-deal'ile.
2. Sales-detector liigutab kupongi lunastanud test-deal'i staadiumisse
   Näidis tellitud ja päris ostu Won'i.
3. Cron-kirjed on paigas ja faas 2 läbib otsast lõpuni: see on kogu
   projekti valmis-kontroll.
