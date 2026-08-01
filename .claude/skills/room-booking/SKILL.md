---
name: room-booking
description: Broneeri Tehnopoli seminariruum (vaikimisi Investor Lounge, Mäealuse 2/1) sisemise e-kirja soovi peale, koodiga KVincubator ja AINULT 0-eurose summaga. Käivitatakse headless'ina room_booking_watch.py poolt argumendiga = spool-faili tee. Kasuta, kui kasutaja palub broneerida seminariruumi või käivitab /room-booking <spool.json>.
---

# room-booking — Tehnopoli seminariruumi broneerija

Sisend: argument on JSON spool-fail kujul
`{"id": <graph msg id>, "from": <saatja>, "subject": ..., "received": ..., "body_text": <puhas tekst>}`.
Loe see fail; selles on ühe @nanordica.com saatja ruumibroneerimise soov.

## RAUDSED REEGLID (enne kõike)

1. **AINULT tasuta broneering.** `tehnopol_client.book_room` kontrollib enne
   tellimust ostukorvi kogusummat Store API kaudu ja keeldub, kui see ei ole
   täpselt 0 (`error: "nonzero_total"`). ÄRA kunagi seda väravat möödu, ära
   sisesta makseandmeid ega ava makselehte. Mistahes summa > 0 → broneeringut
   EI tehta, vasta saatjale veateatega.
2. **Kood `KVincubator`** rakendub kliendis automaatselt (`apply_coupon`) —
   ilma selleta on ruum lukus ja hind tasuline.
3. Saatja peab olema `@nanordica.com` (watcher juba filtreerib; kontrolli üle).
4. Ainult Mäealuse 2/1 ruumid (kataloog allpool). Kood KVincubator kehtib
   nende peal; teisi maju ÄRA broneeri.
5. Kui kirjast puudub kuupäev või kellaaeg → ÄRA broneeri; vasta täpsustava
   küsimusega (millal, kui pikalt, mitu inimest).
6. Kui soovitud aeg on valitud ruumis hõivatud ("Kinni") → ÄRA vali teist
   aega omavoliliselt; kontrolli sama aja peale teisi sobivaid ruume
   (kataloog) ja vasta saatjale valikutega, mida päriselt nägid.

## Mäealuse 2/1 ruumide kataloog (kontrollitud 29.07.2026)

| Ruum | Mahutavus | slug (kliendile) |
|---|---|---|
| Kosmos | 4 | `kosmos` |
| Prototron | 4 | `prototron` |
| Ruutu6 | 4 | `ruutu6` |
| Swedbank | 7 | `swedbank` |
| Investor Lounge | 10 | `investorlounge` |
| UK Lounge | 30 | `uk-lounge` |

(sama kataloog koodis: `tehnopol_client.ROOMS`)

## Soovitüübi tuvastus ja ruumivalik

Kirjast võib tulla kolme tüüpi soove — käsitle vastavalt:

**A. Ruum nimetatud** ("broneeri Investor Lounge reedeks 15–16") → kasuta
seda ruumi.

**B. Inimeste arv, ruumi pole** ("vaja ruumi 6 inimesele neljapäeval 14–15")
→ valikureegel:
- **≥3 inimest → eelista ALATI Swedbanki (7) või Investor Lounge'i (10)**:
  3–7 → Swedbank, kui vaba, muidu Investor Lounge; 8–10 → Investor Lounge;
  11–30 → UK Lounge. Väiksemaid (Kosmos/Prototron/Ruutu6) sel juhul ise ÄRA
  broneeri — võid neid vastuses ALTERNATIIVINA mainida ("kui eelistate
  väiksemat, on kell X vaba ka Kosmos — vasta 'broneeri Kosmos'").
- 1–2 inimest → KA siis eelista Swedbanki/Investor Lounge'i, kui need on
  sel ajal vabad (väikesed ruumid maini alternatiivina); väike ruum
  (Kosmos/Prototron/Ruutu6) vali ainult siis, kui mõlemad eelistatud on
  kinni.
- Inimeste arvu EI ole ja ruumi EI ole nimetatud → vaikimisi Investor
  Lounge.
- Kui eelistatud ruumid on soovitud ajal kinni, ütle vastuses ausalt, mis
  oli kinni ja mille asemel valisid/pakud.

**D. Broneering + kutsed** ("pane koosolekuruum kinni ja saada kutsed
mart@…, vera@…, külaline@partner.ee") → inimeste arv = kutsutavate arv + 1
(saatja ise). Vali ruum B-reegli järgi, broneeri Tehnopolis (sama 0,00 €
värav), ja SEEJÄREL saada kalendrikutsed repo juurest:
`cd mcp && set -a; . ./.env; set +a` ning python:
`from lib import graph_client as gc; gc.create_event("<start UTC ISO>", "<end UTC ISO>", "<teema kirjast või 'Koosolek'>", ["<saatja>", "<kutsutav1>", ...], body_text="Ruum: <ruum>, Mäealuse 2/1 (Tehnopol). Broneeritud koodiga KVincubator, 0,00 EUR.", location="<Ruum>, Mäealuse 2/1, Tehnopol")`
— korraldaja on ravimus@, kutse läheb KA saatjale endale. NB kellaajad
UTC-s (EEST − 3h). Kutsed saada AINULT pärast õnnestunud 0-eurost
broneeringut; kui broneering ebaõnnestus, kutseid ei lähe. Kutsutavad
võivad olla ka välised aadressid (tavaline koosolekukutse). Vastuses
kinnita mõlemad: ruum broneeritud + kutsed saadetud (kellele).

**Ajareegel "kui <inimene> on vaba":** kui kirjas pole kellaaega, vaid
tingimus stiilis "esimesel ajal, kui Meelis on vaba" → leia Meelise
(GRAPH_CALENDAR_USER) vabad ajad repo juurest: `cd mcp && set -a; . ./.env;
set +a` ja python: `from lib import graph_client as gc;
gc.get_free_slots("<täna>T00:00:00Z", "<täna+2p>T23:59:59Z", 60)` —
tagastab UTC slotid (EEST = UTC+3). Võta esimene TULEVIKUS olev slot, mis
on ka valitud ruumi kalendris vaba; kui päev saab otsa, liigu järgmisele
tööpäevale. Kestus määramata → eelda 1 tund. Sama slot broneeri Tehnopolis
ja kasuta kutsete ajana.

**C. Vabaduse päring** ("mis ruum on homme kell 14 vaba?") → küsi seis
`tc.find_free_rooms(<kuupäev>, <algus>, <lõpp>, min_capacity=<inimesi või 1>)`
(kontrollib kõiki sobivaid ruume korraga). Seejärel:
- kui kirjas on selge korraldus stiilis "broneeri (see) ära" / "lase üle
  broneerida" → broneeri parim vaba (väikseim-sobiv reegel) ja kinnita;
- muidu ÄRA broneeri — vasta nimekirjaga "kell X on vabad: …" ja paku, et
  vastusega "broneeri <ruum>" teed broneeringu ära (see vastus jõuab
  watcheri kaudu uue soovina tagasi).

## Broneerimisvoog (repo-sisene HTTP-klient — brauserit EI vajata)

Kõik käib `mcp/lib/tehnopol_client.py` kaudu (puhas stdlib HTTP; retsept
pöördprojekteeritud ja elusalt kinnitatud 01.08.2026). Käivita repo juurest:
`cd mcp && set -a; . ./.env; set +a` ja siis python.

**Vabade aegade vaatamine** (kõik Mäealuse 2/1 ruumid korraga):
```python
from lib import tehnopol_client as tc
tc.find_free_rooms("2026-08-03", "14:00", "15:00", min_capacity=3)
# -> [{"slug","name","capacity","free":bool,"bookings":[...]}, ...]
```

**Ühe ruumi päeva vabad aknad:**
```python
s = tc.Session(); room = tc.open_room(s, "swedbank")
tc.apply_coupon(s, room["product_id"])            # KVincubator
day = tc.availability(s, room["product_id"], "2026-08-03").get("2026-08-03", [])
tc.free_slots(day, duration_min=60)               # -> [{"start","end"}, ...]
```

**Broneerimine** (üks kõne teeb kogu ahela: leht → kupong → saadavus →
ostukorv → **0-euro värav** → tellimus):
```python
tc.book_room("swedbank", "2026-08-03", "14:00", "15:00",
             first_name="Meelis", last_name="Kadaja",
             email="meelis@nanordica.com", phone="+372 5184872",
             company="Nanordica Medical OÜ", dry_run=False)
# õnnestumisel: {"booked": True, "order_id": ..., "room","date","start","end"}
```

Tagastuse tõlgendus:
- `booked: True` → broneering tehtud, `order_id` on Tehnopoli tellimusenumber
- `error: "slot_taken"` → aeg hõivatud; väljal `free` on sama päeva vabad
  aknad, `bookings` näitab hõivatud vahemikke → paku need saatjale
- `error: "nonzero_total"` → **broneeringut EI tehtud** (raudne reegel);
  vasta saatjale, et hind polnud 0,00 € ja broneering jäi tegemata
- muu `error` → kirjelda ausalt, ära proovi mööda hiilida

`dry_run=True` teeb kõik sammud kuni tellimuseni (sh 0-euro kontroll), aga
tellimust ei vormista — kasuta, kui tahad ainult veenduda, et aeg ja hind
klapivad.

## Vastus saatjale

Saada vastus SAMA lõime sisse Graph'iga (repo juurest):
`cd mcp && set -a; . ./.env; set +a` ja python one-liner:
`from lib import graph_client as gc; gc.reply_mail("<spool id>", "<html>")`
(fallback `gc.send_mail(saatja, teema, html)`).

- Õnnestus: kinnita ruum + kuupäev + kellavahemik + "kood KVincubator, summa
  0,00 €" + märgi, et Tehnopoli kinnitusmeil (muutmis/tühistuslingiga) tuleb
  tema aadressile.
- Aeg kinni: loetle kalendrist nähtud vabad ajad samal päeval.
- Andmed puudu: küsi kuupäev + kellaaeg + kestus.
- Viga (sh mistahes summa ≠ 0,00 €): kirjelda ausalt, mida nägid; ära broneeri.

## Lõpetamine

Tõend on `order_id` (Tehnopoli tellimusenumber) — pane see nii vastuskirja
kui result-faili. Kirjuta spool-faili kõrvale `<spool>.result.json`:
`{"status": "booked|options|clarification|busy|error", "room": ..., "start": ..., "end": ..., "reply_sent": true/false, "detail": ...}`
("options" = vabaduse-päringule saadeti valikute nimekiri ilma broneerimata).
See on watcheri jaoks — tema märgib kirja registrisse. Kui sa result-faili ei
kirjuta, loeb watcher katse ebaõnnestunuks ja proovib järgmisel tsüklil uuesti.
