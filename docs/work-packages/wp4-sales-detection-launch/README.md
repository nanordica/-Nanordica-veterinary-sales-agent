# wp4: müügituvastus, ajastus ja lõpptest

**Omanik:** Karmen Tigas (product, partnerships)
**Disaini sammud:** 6, 8 ([ehitusjärjekord](../../ravimus-lead-pipeline-design.md#ehitusjärjekord))

## Missioon

Sulge lehtri lõpp ja vii süsteem käiku: ravimus serveri wix-tööriistad
näevad tellimusi ja loovad personaalseid kuponge (kiht ise on Mardi
oma), sales-detector seob ostud deal'idega, cron paneb
rütmi paika ning sina koordineerid mõlemat testifaasi. Tootepool on sinu
valdkond, `lv-vet-email-funnel` skill koos tootefaktidega on juba sinu
harust mestitud.

## Tulemid

- [x] Wix-tööriistad: tellimuste loetelu, personaalse kupongi loomine
      (sh 100% näidisekupong), kupongi kasutuse kontroll; hindade muutmist
      ja tagasimakseid ei avata
      ([tööriistakiht](../../ravimus-lead-pipeline-design.md#tööriistakiht--kohalikud-mcp-serverid)).
      Elavad ravimus serveris (`mcp/tools/wix.py`, ühine kiht Mardiga;
      eraldi wix-mcp sai dubleerimise vältimiseks maha võetud). Live-kõnede
      kontroll on Mardil, kelle masinas võtmed on:
      [tookask-mart-wix-live-check.md](tookask-mart-wix-live-check.md).
- [x] `.claude/agents/sales-detector.md`: pollib Wixi, seob ostja e-posti
      või kupongikoodi deal'iga; päris ost → Won + tänukiri, näidise
      lunastus → Naidis tellitud + `sample_claimed_at`; seostumatu
      tellimus logitakse
      ([sales-detector](../../ravimus-lead-pipeline-design.md#sales-detector)).
      Ühendatud ravimus serveri tööriistadele; deal'i-sidumise läbiproov
      käib võtmetega masinas (Mart), sammud on valmis:
      [sales-detector-integration-test.md](sales-detector-integration-test.md).
- [x] Cron: tikk iga 30 min (`claude -p "/tick"`), discovery kord nädalas —
      `scripts/install-cron.sh` (testitud: paigaldus/eemaldus). Võib
      paigaldada kohe: mõlemal kirjel on guard, tikk käivitub alles
      siis, kui wp1 `/tick` skill repos olemas on
- [ ] Faas 1, DRY_RUN: täisjooks päris registri peal, kirju saatmata;
      kogu tiim vaatab logid üle (kirjade kvaliteet, sihtimine, redel),
      sina koordineerid — sammud: [launch-checklist.md](launch-checklist.md)
      ([testimine](../../ravimus-lead-pipeline-design.md#testimine-ja-valmis-definitsioon))
- [ ] Faas 2, sünteetiline lead: sina oled "vet" registri CSV-s ja läbid
      kogu tee Discovered → Won (saad esmakirja, vastad küsimusega, saad
      pakkumise, ostad Wixis); deal liigub Won'i ilma inimsekkumiseta —
      sammud: [launch-checklist.md](launch-checklist.md)

## Sõltuvused

Sales-detector vajab ravimus serverit (wp1, main'is olemas) ning päris
jooksuks Wixi + Pipedrive'i võtmeid, mis on ainult Mardi masinas — kuni
siis DRY_RUN. Faas 1 vajab kõiki nelja paketti, seega planeeri see
viimasesse pooltundi ja hoia tiimi ajakaval.

## Valmis, kui

1. Ravimus serveri wix-tööriistad läbivad live-kontrolli (töökäsk,
   issue #7): tellimuste loetelu + 100% näidisekupongi loomine.
2. Sales-detector liigutab kupongi lunastanud test-deal'i staadiumisse
   Naidis tellitud ja päris ostu Won'i.
3. Cron-kirjed on paigas ja faas 2 läbib otsast lõpuni: see on kogu
   projekti valmis-kontroll.
