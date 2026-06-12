# Faas 2: sünteetilise "veti" andmed (Karmen)

Discovery jooks (Meelise masinas, võtmed seal) lisab selle rea registri andmetesse enne faasi 2
jooksu, samas formaadis, mis päris registrist parsitud read
(`cache/registry.csv`). Täpne veerustruktuur selgub wp1
discovery-sammus; siin on väärtused, mis rida kandma peab.

| Väli | Väärtus | Miks |
|---|---|---|
| `registry_id` | `SYNTH-KARMEN-001` | selgelt sünteetiline, dedup ei põrku päris ID-dega ja rea leiab pärast kergesti üles |
| nimi | Karmen Tigas | päris vastaja peab kirja ära tundma |
| e-post | `karmen@kood.tech` | ainus aadress, mille mail-mcp allowlist faasis 2 lubab |
| kliinik | Rīgas dzīvnieku neatliekamās palīdzības klīnika (kiirabikliinik) | kiirabikliinik on skoorimisrubriigis kõrgeima kaaluga: rida peab kindlalt läve (30) ületama ja pingerea tippu jõudma, muidu outreach ei võta seda esimese partiiga |
| eriala | väikeloomad, haavaravi/kirurgia | rubriigi ülejäänud signaalid samale poole |
| keel/asukoht | Riia, Läti | kiri peab tulema läti keeles nagu päris vetile |

## Reeglid

- Rida lisatakse AINULT faasi 2 jooksuks ja eemaldatakse enne faasi 3
  (live). `SYNTH-` prefiks on eemaldamise otsingumuster.
- Kui discovery jookseb cache'itud registrifaili pealt, lisa rida
  cache'i, mitte allalaadimiskoodi sisse.
- Enrichment selle "veti" kohta veebist midagi ei leia — see on
  taotluslik ja testib ühtlasi disaini reeglit, et profiilita deal
  liigub edasi minimaalse profiiliga.
- Enne `DRY_RUN=0`: Annelis (wp3) kinnitab, et mail-mcp lubab AINULT
  aadressi `karmen@kood.tech`.

Faasi 2 sammud tervikuna: [launch-checklist.md](launch-checklist.md).
