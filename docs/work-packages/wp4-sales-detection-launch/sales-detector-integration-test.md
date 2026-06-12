# Sales-detectori integratsioonitest (wp4 "Valmis, kui" punkt 2)

Eeldab ravimus serverit, milles on Pipedrive'i token JA Wixi võtmed —
ehk Meelise masinat (Karmeni masinas võtmeid pole). Kõik kirjutused
käivad `DRY_RUN=1`-ga, st server ainult logib need (`dry_log`); päris
Pipedrive'i/Wixi midagi ei muudeta.

## Ettevalmistus

1. Ravimus server jookseb, `pipedrive_setup` on jooksutatud
   (stage-kaart olemas), `DRY_RUN=1`.
2. Vaata `wix_list_orders(limit=5)` väljundist üks PÄRIS tellimus ja
   selle ostja e-post. Kui poes pole ühtegi tellimust, tee Wixis üks
   väike testost (või lükka see test faasi 2, kus Karmen ostab
   "vetina" nagunii).
3. Loo Pipedrive'i UI-s test-deal staadiumis Contacted, mille
   `_state.email` (JSON-olekuväljas) on sama ostja e-post, pealkiri
   "SYNTH integratsioonitest". (DRY_RUN=1 korral MCP kaudu deal'i
   luua ei saa — loomine logitaks ainult.)

## Jooks

Käivita Claude Code'is: "käivita sales-detector".

## Oodatav tulemus

- [ ] sales-detector leiab tellimuse ja seob selle test-deal'iga
      e-posti järgi
- [ ] `dry_log` kirjed: `pipedrive_move_deal_stage(<deal>, "Won")` +
      note tellimuse numbri ja summaga (DRY_RUN tõttu päris muutust
      ei toimu — see ongi oodatud)
- [ ] `cache/sales-detector-cursor.json` olemas, `last_seen_at` =
      uusima tellimuse aeg
- [ ] korduskäivitus EI plaani sama liigutust uuesti (kursor)
- [ ] seostumatu tellimus (mõni poe tellimus, millel deal'i pole) →
      rida failis `logs/unmatched-orders.md`, deal'e ei plaanita
      muuta

Kupongiraja (näidise lunastus → Naidis tellitud) täismahus kontroll
jääb faasi 2: Karmen lunastab sünteetilise lead'ina päris 100%
kupongi ja deal peab liikuma ilma inimsekkumiseta.

Pärast testi kustuta test-deal.
