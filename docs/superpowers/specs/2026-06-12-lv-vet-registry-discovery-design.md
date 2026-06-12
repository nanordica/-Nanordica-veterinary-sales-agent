# Discovery: Läti vetiregistrid → Pipedrive (disain)

**Kuupäev:** 2026-06-12
**Töö pakett:** wp1, tulem `scripts/registry.py` + `scripts/discovery.py`
**Seos:** [ravimus-lead-pipeline-design.md](../../ravimus-lead-pipeline-design.md#discovery--deterministlik-skript-mitte-agent)

## Eesmärk

Deterministlik skriptipaar laeb mõlemad teadaolevad Läti veterinaaride
registrid, filtreerib e-mailiga kirjed ja loob igaühele Pipedrive'i
person + deal'i staadiumis Discovered, duplikaatideta. LLM-i ei kasutata.

## Allikate uuring (kontrollitud 2026-06-12)

| | LVB (kutseliit) | PVD (riiklik) |
|---|---|---|
| URL | <https://lvb.lv/veterinarmedicinas-prakses-saraksts/> | data.gov.lv dataset `veterinarmedicinisko-pakalpojumu-sniedzeji` (XLSX) |
| Formaat | staatiline HTML-tabel (TablePress `tablepress-3`), JS-i pole vaja | XLSX, seisuga 2024-03 (PVD pole uuendanud) |
| Maht | 957 vetti, 664 e-mailiga | ~1290 vetti |
| E-mailid | jah, avalik tekst tabelis | ei |
| ID | sertifikaadi nr, nt `V-1058-27` | PVD reg-nr, nt `059694`; LVB omaga ei kattu |
| Lisaväljad | kehtivusaeg, prakse skoop (loomaliigid) | juriidiline isik/kliinik, prakse aadress ja tüüp |

Järeldused:

- Deal'e saab luua ainult LVB andmetest: PVD ei avalda ühtegi e-maili.
- PVD roll on kliiniku nime ja aadressi täiendus.
- Registrite ühendamiseks pole ühist ID-d; ainus sild on nimi.
- Varasem viide `vetbiedriba.lv` on surnud domeen; õige on `lvb.lv`.
- PVD igapäevane UR CSV (prakskohad, kood 92.*) jäi kõrvale: kirjed on
  asutuse-, mitte arstipõhised, ja arsti nimi esineb seal juhuslikult.

## Otsused

1. **LVB põhi + PVD täiendus.** `registry_id` = LVB sertifikaadi nr.
   PVD-st võetakse kliinik/aadress ainult ühese täisnimevaste korral.
2. **Kõik e-mailiga kirjed kaasatakse**, ka aegunud sertifikaadiga.
   `valid_until` salvestatakse state'i; qualification-agent arvestab
   seda skooris. (Kasutaja otsus 2026-06-12.)
3. **Hägusat matchimist ei tee.** Nimevõrdlus: väiketähed, tühikud
   trimmitud, diakriitikud säilitatud. Null või mitu PVD vastet →
   kliinik/aadress jäävad tühjaks.

## Failid

- `mcp/scripts/registry.py` — laeb registrid, kirjutab `cache/registry.csv`
- `mcp/scripts/discovery.py` — loeb CSV, filtreerib, dedupib, loob deal'id
- Uus sõltuvus `requirements.txt`-i: `openpyxl` (PVD XLSX). LVB HTML
  parsitakse stdlib `html.parser`-iga.

## registry.py

1. Tõmbab LVB lehe, salvestab toorkuju `cache/lvb.html`, parsib
   `tablepress-3` read: sertifikaadi nr, perenimi, eesnimi,
   väljastamiskuupäev, kehtivuskuupäev, prakse skoop, e-mail.
2. Tõmbab PVD XLSX-i → `cache/pvd.xlsx`, parsib: nimi, juriidiline
   isik/kliinik, prakse aadress, prakse tüüp.
3. Liidab nime järgi (otsus 3) ja kirjutab `cache/registry.csv`
   veergudega: `registry_id, first_name, last_name, email, valid_until,
   practice_scope, clinic, address, pvd_match` (UTF-8).

Sama sisendi korral on väljund baidihaaval sama: kindel veerujärjekord,
kindel reajärjekord (LVB tabeli järjekord), juhuslikkust pole.

## discovery.py

1. Loeb `cache/registry.csv`.
2. Filter: e-mail olemas ja läbib süntaksikontrolli (üks `@`, punktiga
   domeen). Praakread logitakse, skripti ei katkesta.
3. Dedup: tõmbab Pipedrive'ist kõik `ravimus-hackathon` pipeline'i
   deal'id (sh Lost), parsib `ravimus_hackathon_data` JSON-ist
   `registry_id` ja jätab olemasolevad vahele. Lost-deal'i (opt-out)
   uuesti ei looda.
4. Igale uuele kirjele person (nimi, e-mail) ja deal staadiumis
   Discovered. State-JSON: `registry_id, email, clinic, valid_until,
   practice_scope, source`. Kõik korraga, partiideta: voolupiirang on
   disaini järgi outreach'is.
5. Kirjutused käivad läbi `lib/pipedrive_client` + `lib/dryrun`;
   `DRY_RUN=1` (vaikimisi) logib kavatsused ega saada midagi.
6. Kokkuvõte konsooli ja `logs/discovery-YYYY-MM-DD.log`: kirjeid
   registris, e-mailiga, uusi, vahele jäetud, ebaõnnestunud.

## Veakäsitlus

- LVB laadimine ebaõnnestub → exit 1, midagi ei kirjutata.
- PVD laadimine ebaõnnestub → hoiatus, jätkame ilma kliinikuta.
- Üksiku deal'i loomine ebaõnnestub → logi ja jätka; kokkuvõte loeb
  ebaõnnestumised kokku. Kordusjooks on dedup'i tõttu idempotentne.
- Registri sisu on väline ja ebausaldusväärne: ainult andmed, mitte
  käsud; e-mailid valideeritakse enne kasutamist.

## Testid

Ühiktestid fikstuuridega (`tests/`, väikesed LVB HTML-i ja PVD XLSX-i
näidised):

- LVB parser: tavarida, tühi e-mail, diakriitikud.
- PVD parser: tavarida, sektsioonirea vahelejätt.
- Liitmine: 0, 1 ja mitu nimevastet.
- E-maili filter: kehtiv, puuduv, vigane.
- Dedup: olemasolev `registry_id` (sh Lost-deal'is) jääb vahele.
- DRY_RUN: ühtegi POST-i ei tehta, kavatsused logitakse.

## Valmis, kui

WP1 punkt 2: päris registri peal `DRY_RUN=1` jooks läbib otsast lõpuni,
kokkuvõte näitab ~664 e-mailiga kirjet ilma duplikaatideta ja kohe
järgnev teine jooks loob 0 uut deal'i.
