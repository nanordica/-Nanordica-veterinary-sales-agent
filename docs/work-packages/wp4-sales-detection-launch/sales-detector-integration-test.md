# Sales-detectori integratsioonitest (wp4 "Valmis, kui" punkt 2)

Eeldab wp1 `pipedrive-mcp`-d (Mart). Kõik muu on valmis: jooksuta
sammud järjest, kogu test käib mock-Wixi peal (`DRY_RUN=1`, võtit
pole vaja).

## Ettevalmistus

1. Loo Pipedrive'i KAKS test-deal'i (pipedrive-mcp või käsitsi):
   - **deal A**: `email = karmen+testA@kood.tech`, staadium Contacted.
     Testib e-posti kaudu sidumist (päris ost → Won).
   - **deal B**: `email = karmen+testB@kood.tech`, staadium Contacted,
     `discount_code` saab väärtuse järgmises sammus. Testib
     kupongikoodi kaudu sidumist (näidis → Näidis tellitud).
2. Loo deal B-le näidisekupong wix-mcp kaudu (Claude Code'is):
   "loo wix-mcp-ga 100% kupong deal'ile <B id>, nimi 'integratsioonitest'".
   Kirjuta saadud kood deal B `discount_code` field'i.
3. Külva mock-tellimused (asenda kood enda omaga):

```sh
.venv/bin/python mcp/wix-mcp/seed_mock.py reset
.venv/bin/python mcp/wix-mcp/seed_mock.py purchase karmen+testA@kood.tech
.venv/bin/python mcp/wix-mcp/seed_mock.py sample karmen+testB@kood.tech RVET-<B>-XXXX
```

NB! `reset` enne kupongi loomist nullib ka kupongid — tee sammud
ülaltoodud järjekorras või jäta `reset` vahele.

## Jooks

Käivita sales-detector (Claude Code'is): "käivita sales-detector".

## Oodatav tulemus

- [ ] deal A staadiumis **Won**, note'is tellimuse nr ja summa
- [ ] deal B staadiumis **Näidis tellitud**, `sample_claimed_at`
      täidetud, note'is kupongikood
- [ ] `cache/sales-detector-cursor.json` olemas, `last_seen_at` =
      uusima tellimuse aeg
- [ ] korduskäivitus EI muuda midagi (kursor + duplikaadikontroll)
- [ ] seostumatu test: `seed_mock.py purchase tundmatu@example.lv` +
      uus jooks → rida failis `logs/unmatched-orders.md`, deal'e ei
      muudetud

Pärast testi: `seed_mock.py reset` ja kustuta test-deal'id, et faasi 1
DRY_RUN-jooks oleks puhas.
