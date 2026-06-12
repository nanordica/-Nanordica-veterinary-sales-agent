# Testifaaside kontroll-leht (wp4)

Karmen koordineerib. Alus:
[testimine ja valmis-definitsioon](../../ravimus-lead-pipeline-design.md#testimine-ja-valmis-definitsioon).

## Eeldused enne faasi 1

- [ ] wp1: `pipedrive-mcp` smoke-test läbib, pipeline + staadiumid +
      field'id Pipedrive'is olemas
- [ ] wp1: discovery on registri deal'idena sisse laadinud
- [ ] wp2: enrichment + qualification jooksevad päris Discovered
      deal'ide peal
- [ ] wp3: `mail-mcp` DRY_RUN-is, outreach-writer + keelekontroll
      annavad lätikeelse kirja
- [ ] wp4: `wix-mcp` smoke-test läbib
      (`.venv/bin/python mcp/wix-mcp/smoke_test.py`)
- [ ] Mart: `wix-mcp` live-kontroll läbitud oma masinas, väljund PR #6
      kommentaaris ([töökäsk](tookask-mart-wix-live-check.md))
- [ ] `/tick` skill olemas (wp1) ja cron paigaldatud
      (`scripts/install-cron.sh`)
- [ ] `.env`-is `DRY_RUN=1`

## Faas 1: DRY_RUN täisjooks

Jooks: `claude -p "/tick"` käsitsi (mitte croni oodata), seejärel
loevad KÕIK NELI logid üle.

- [ ] tikk lõpetas, kokkuvõte `logs/tick-*.md` olemas
- [ ] `logs/dry-run-*.md`: iga kavandatud kiri/kupong/staadiumimuutus
      kirjas, päris süsteeme ei puudutatud
- [ ] kirjade kvaliteet: läti keel korrektne (Annelis), tootefaktid
      ainult `product-ravimus-vet.md`-st (Meelis), personaliseerimine
      asjakohane (Karmen)
- [ ] sihtimine: ainult Qualified pingerea tipp, Contacted < 20
      (Mart)
- [ ] redel: vahed 3/5/8/13, max 5 kirja, opt-out blokeerib
- [ ] vead üle vaadatud: `logs/errors.md` tühi või selgitatud

## Faas 2: sünteetiline lead (projekti valmis-kontroll)

Karmen on "vet": tema rida registri CSV-s, DRY_RUN väljas, mail-mcp
lubab AINULT tema aadressi. Sünteetilise rea andmed wp1 jaoks:
[faas2-synteetiline-vet.md](faas2-synteetiline-vet.md).

- [ ] mail-mcp allowlist: ainult Karmeni e-post (wp3 kinnitab enne
      DRY_RUN=0 keeramist!)
- [ ] `DRY_RUN=0`, cron sees
- [ ] discovery loob deal'i: Discovered
- [ ] enrichment + qualification: Qualified
- [ ] esmakiri saabub: lätikeelne, personaalse Wixi lingiga, A/B
      variant field'is, loobumisrida olemas -> Contacted
- [ ] Karmen vastab küsimusega -> inbox-triage: Engaged
- [ ] sisuline vastus + pakkumine personaalse koodiga saabub
- [ ] Karmen ostab Wixis -> sales-detector: Won, ilma inimsekkumiseta
- [ ] tänukiri saabub
- [ ] deal'i note'ides on kogu kirjavahetus

Kui kõik linnukesed käes: faas 3 (live) on tiimi ühine otsus, mitte
automaatne järgmine samm.
