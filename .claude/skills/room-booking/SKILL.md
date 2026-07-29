---
name: room-booking
description: Broneeri Tehnopoli seminariruum (vaikimisi Investor Lounge, Mäealuse 2/1) sisemise e-kirja soovi peale, koodiga KVincubator ja AINULT 0-eurose summaga. Käivitatakse headless'ina room_booking_watch.py poolt argumendiga = spool-faili tee. Kasuta, kui kasutaja palub broneerida seminariruumi või käivitab /room-booking <spool.json>.
---

# room-booking — Tehnopoli seminariruumi broneerija

Sisend: argument on JSON spool-fail kujul
`{"id": <graph msg id>, "from": <saatja>, "subject": ..., "received": ..., "body_text": <puhas tekst>}`.
Loe see fail; selles on ühe @nanordica.com saatja ruumibroneerimise soov.

## RAUDSED REEGLID (enne kõike)

1. **AINULT tasuta broneering.** Broneeringu kokkuvõttes PEAB olema `Kokku: 0,00 €`
   JA nupp PEAB olema **"Broneeri"**. Kui näed nuppu "Suundu maksma" või mistahes
   summat > 0,00 € — KATKESTA kohe, ära kliki midagi, vasta saatjale veateatega.
   Mitte kunagi ära sisesta makseandmeid ega jätka makselehele.
2. **Alati aktiveeri kood `KVincubator`** enne aja valimist — ilma koodita on
   kalender lukus ja hinnad tasulised.
3. Saatja peab olema `@nanordica.com` (watcher juba filtreerib; kontrolli üle).
4. Ainult Mäealuse 2/1 ruumid (kataloog allpool). Kood KVincubator kehtib
   nende peal; teisi maju ÄRA broneeri.
5. Kui kirjast puudub kuupäev või kellaaeg → ÄRA broneeri; vasta täpsustava
   küsimusega (millal, kui pikalt, mitu inimest).
6. Kui soovitud aeg on valitud ruumis hõivatud ("Kinni") → ÄRA vali teist
   aega omavoliliselt; kontrolli sama aja peale teisi sobivaid ruume
   (kataloog) ja vasta saatjale valikutega, mida päriselt nägid.

## Mäealuse 2/1 ruumide kataloog (kontrollitud 29.07.2026)

| Ruum | Mahutavus | URL |
|---|---|---|
| Kosmos | 4 | https://www.tehnopol.ee/ruum/kosmos/ |
| Prototron | 4 | https://www.tehnopol.ee/ruum/prototron/ |
| Ruutu6 | 4 | https://www.tehnopol.ee/ruum/ruutu6/ |
| Swedbank | 7 | https://www.tehnopol.ee/ruum/swedbank/ |
| Investor Lounge | 10 | https://www.tehnopol.ee/ruum/investorlounge/ |
| UK Lounge | 30 | https://www.tehnopol.ee/ruum/uk-lounge/ |

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

**C. Vabaduse päring** ("mis ruum on homme kell 14 vaba?") → ava
kandidaatruumide lehed (mahutavuse-vihje olemasolul ainult sobivad, muidu
kõik), aktiveeri igal kood, loe kalendrist soovitud aja seis. Seejärel:
- kui kirjas on selge korraldus stiilis "broneeri (see) ära" / "lase üle
  broneerida" → broneeri parim vaba (väikseim-sobiv reegel) ja kinnita;
- muidu ÄRA broneeri — vasta nimekirjaga "kell X on vabad: …" ja paku, et
  vastusega "broneeri <ruum>" teed broneeringu ära (see vastus jõuab
  watcheri kaudu uue soovina tagasi).

## Broneerimisvoog (Steel guided-browser; retsept verifitseeritud 29.07.2026)

Tööriist: `python3 ~/.hermes/scripts/browserless-guided.py` (alias BG). Pordiks
vali 9232. Iga `act` vastus on JSON; `ok:false` korral vaata
`/tmp/bl-guided/port-9232.log` ja tee snapshot. Lõpus ALATI `stop --port 9232`
(mitte kunagi pkill).

1. `BG start --port 9232 --minutes 25 <valitud ruumi URL kataloogist>`
   (mitme ruumi kontrolliks kasuta sama sessiooni: `act --port 9232 goto <järgmise ruumi URL>` — kood tuleb igal lehel uuesti aktiveerida)
2. `BG act --port 9232 accept-cookies` (või `click "Nõustun"`)
3. `BG act --port 9232 fill "#coupon_code" "KVincubator"` → `click "Aktiveeri"`
   → snapshot: lukuteade "Sisesta kehtiv broneerimiskood" peab olema KADUNUD.
4. Kalender on FullCalendar nädalavaade (E–R, data-date atribuudid).
   Vajadusel liigu õigele nädalale (next-nool: otsi `.fc-next-button` ja kliki).
   Aja valik käib koordinaadi-klikiga, mis PEAB olema viewport'is:
   a. Keri: `eval "(()=>{const l=[...document.querySelectorAll('td.fc-timegrid-slot-lane')].find(t=>t.dataset.time==='<HH-1>:00:00'); l&&l.scrollIntoView({block:'center'}); return 'ok';})()"`
   b. Koordinaadid: `eval "JSON.stringify((()=>{const c=document.querySelector('.fc-timegrid-col[data-date=\"YYYY-MM-DD\"] .fc-timegrid-col-frame').getBoundingClientRect(); const l=[...document.querySelectorAll('td.fc-timegrid-slot-lane')].find(t=>t.dataset.time==='HH:MM:00').getBoundingClientRect(); return {x:Math.round(c.x+c.width/2), y:Math.round(l.y+2)};})())"`
   c. `click-at <x> <y>` — üks klikk valib 30-min sloti algusega sel ajal.
      Pikema aja jaoks kliki järjest ka järgmisi 30-min slotte ja kontrolli
      snapshot'iga, kuidas kokkuvõtte ajavahemik muutub (kui teine klikk
      hoopis tühistab/asendab valiku, vali pikkus nii nagu vidin võimaldab ja
      kirjuta vastusesse tegelik broneeritud vahemik).
5. Snapshot → kontrolli kokkuvõtet: õige kuupäev, ajavahemik, ruum, ja
   REEGLI 1 tingimused (Kokku: 0,00 € + nupp "Broneeri").
6. `click "Broneeri"` → snapshot. Kui avaneb kontaktivorm (Gravity Forms:
   nimeväli `#input_1_4`, e-post `#input_1_1`, tingimuste checkbox
   `#input_1_3_1`): nimi = saatja nimi või "Nanordica Medical OÜ", e-post =
   **saatja enda aadress** (siis jõuab Tehnopoli kinnitus/muutmislink temani),
   checkbox linnukesse, submit. Snapshot → veendu kinnituses.
7. Tõend: viimane snapshot'i screenshot (snap.png) — kopeeri
   `~/.hermes/logs/room-booking-<msgid8>.png`.
8. `BG stop --port 9232`

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

Kirjuta spool-faili kõrvale `<spool>.result.json`:
`{"status": "booked|options|clarification|busy|error", "room": ..., "start": ..., "end": ..., "reply_sent": true/false, "detail": ...}`
("options" = vabaduse-päringule saadeti valikute nimekiri ilma broneerimata).
See on watcheri jaoks — tema märgib kirja registrisse. Kui sa result-faili ei
kirjuta, loeb watcher katse ebaõnnestunuks ja proovib järgmisel tsüklil uuesti.
