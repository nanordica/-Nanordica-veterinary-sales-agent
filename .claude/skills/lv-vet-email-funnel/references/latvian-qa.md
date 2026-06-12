# Läti keele automaatne kvaliteedikontroll

**Tiimis pole läti keele natiivkõnelejat.** Seega iga läti kiri läbib enne
valmis-märkimist selle automaatse värava. **Ära märgi kirja saatmisvalmiks
enne, kui kõik sammud on tehtud.**

## Aus piirang (loe enne)

Automaatne kontroll **ei asenda täielikult natiivkõnelejat**, eriti
meditsiiniseadme väidete nüansis. Eesmärk: püüda enamik grammatika- ja
sisuvigu. Jääkrisk jääb — vt `latvia-market.md` (meditsiiniseadme reklaam).

## Värava sammud

### 1. Korrektuuri-pass
Loe enda läti tekst üle **range korrektorina**, kontrolli:
- käänded ja pöörded (läti käändesüsteem on rikkalik — see on suurim veaallikas),
- grammatika ja kooskõla,
- loomulik sõnajärg (mitte eesti/inglise kalka),
- meditsiiniterminite õigsus,
- kirjavahemärgid.

Paranda leitud vead ja loe uuesti.

### 2. Tagasitõlke-värav
- Tõlgi valmis läti tekst **tagasi eesti keelde**.
- Võrdle algse briifi/mõttega.
- Kui tähendus on triivinud, kadunud või moondunud → **genereeri läti tekst
  uuesti** ja korda väravat.

### 3. Väite-kontroll
- Kontrolli, et kõik tootevväited vastavad `product-ravimus-vet.md`-le.
- Ükski väide ei tohi olla tugevam kui tõend lubab.
- Eemalda iga väide, mida product-fail ei kata.

### 4. Valikuline väline tööriist (kõva värav)
Kui kasutaja soovib kõvemat kontrolli:
- **LanguageTool** (`lv`) — grammatika/spelling API,
- **hunspell** sõnastikuga `lv_LV` — spelling.

Need on valikulised; põhiväravaks on sammud 1–3.

## Väljund

Märgi iga valmis kiri:
- ✅ `Läti QA: korrektuur + tagasitõlge tehtud`
- kui mõni väide on kahtlane: ⚠️ märgi see eraldi kasutajale üle vaatamiseks.
