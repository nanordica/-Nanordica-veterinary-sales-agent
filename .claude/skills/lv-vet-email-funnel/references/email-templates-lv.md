# Läti kirja-mallid ja jada-loogika

**Avatud külm jada**, läti keeles, tekstipõhine, CTA viib tootelehele.
Jada **ei lõpe fikseeritud arvu juures**. Jätka kuni vastus (ka "ei"),
opt-out või bounce.

Kõik allolev läti tekst on **mustand, mis peab läbima automaatse QA värava**
(`latvian-qa.md`) enne valmis-märkimist. Natiivkõnelejat tiimis pole.

## Iga kirja reeglid

- **Avarida = kõige konkreetsem tõde** kontaktist (eelistatult tootega seotud
  teenus: kirurgia, haavaravi, operatsioonijärgne hooldus), mitte üldine
  liigi-mainimine ega toode. Pingerida: vt `personalization.md`.
- **Üks CTA** kirja kohta, **kindel ja käskiv** ("Vaata lähemalt siit" /
  "Apskatiet tuvāk šeit"), mitte küsiv ("kas soovite?").
- Saatja päris inimese nimi.
- **Iga kiri toob uut infot.** Ära korda eelmist. Kui uut haaki pole, ära saada.
- **Loobumine = sõbralik rida kirja kõige lõpus**, allkirja järel, CTA-st
  eraldi. Mitte üleskutse, mitte CTA kõrval (vt `cold-outreach.md`).
- Personaliseeri **konkreetse loomaliigi** järgi (`personalization.md`).

## Kirja-nurkade pank (uus haak igas kirjas)

1. **Esmane pöördumine**: üks konkreetne kasu kontakti loomaliigile
2. **Värske teadusartikkel** (enrichmenti kaudu), mis toetab kasutusjuhtu
3. **Juhtumi-näide**: atraumaatiline sidemevahetus loomaliigi kontekstis
4. **Pakkumine**: näidis / proovikomplekt
5. **Sooduskood**: ajaliselt piiratud
6. **Uus nurk**: kuluvõrdlus hõbesidemega, suuruste valik vm
7. **7+**: iga järgnev kiri uus haak; kui haaki pole, ära saada

## Progressiivne ooteaeg

| Saadetud kirju | Paus enne järgmist |
|----------------|--------------------|
| 1 → 2 | 3 päeva |
| 2 → 3 | 4 päeva |
| 3 → 4 | 7 päeva |
| 4 → 5 | 10 päeva |
| 5 → 6 | 14 päeva |
| 6+ | 21–30 päeva |

## Pealkiri + eelvaate-tekst

- Pealkiri lühike (~30–50 tähemärki), konkreetne kasu või uudishimu,
  personaliseeritud (kliinik / loomaliik), väldi rämpssõnu ja CAPS-i.
- Külm pealkiri olgu **vestluslik**, nagu üks-ühele kiri, mitte
  reklaamilöök.
- Eelvaate-tekst täiendab pealkirja, ei korda seda.
- Pealkiri on A/B esmane testimuutuja (`ab-testing.md`).

Pealkirja näited (lv, mustand):
- `{{eesnimi}}, ātrāka brūču dzīšana?`
- `Jautājums par brūču pārsiešanu jūsu klīnikā`
- `Atraumatiska pārsēja maiņa nemierīgiem dzīvniekiem`

## Esmakiri 1 — kinnitatud mall (2026-07-28)

**Pealkiri:** Brūču aprūpes akadēmija: dzīvnieku brūces ar RavimusVET

**Saatja:** Meelis, šūnu biologs, Nanordica Medical

**Avarea variandid (rikastamine valib):**

| Stsenaarium | Tekst |
|---|---|
| Kirurgia | Rakstu Jums, jo {{klīnika}} piedāvā ķirurģiju un pēcoperācijas brūču aprūpi. |
| Innovatsioon | Rakstu Jums, jo esat profesionāli aktīvs un atvērts jauniem risinājumiem. |
| 24h / kiirabi | Rakstu Jums, jo {{klīnika}} diennakts dežūra nozīmē, ka traumatiskas brūces ir Jūsu ikdienas darbs. |
| Kliinikuomanik | Rakstu Jums, jo kā klīnikas īpašnieks Jūs izlemjat, kādus ārstniecības līdzekļus izmantot. |

**Kirja tekst:**

```
Cienījamais/ā Dr. {{uzvārds}},

{{personalizēta rinda}}

Pet City un Evidensia veterinārārsti ir sākuši pārsiet dzīvnieku brūces ar
RavimusVET — arī brūces, kuras iepriekš atstāja vaļā. RavimusVET paātrina
brūces dzīšanu tiktāl, ka tas atsver dzīvnieku brūču pārsiešanas papildu
izaicinājumus. Klīniskā pētījumā ar cilvēkiem brūces laukums samazinājās,
piemēram, par 43% vienas nedēļas laikā RavimusVET grupā, salīdzinot ar 13%
sudraba pārsēja grupā.

Ar dzīvnieku brūču pārsiešanas praksi varat iepazīties Brūču aprūpes
akadēmijā: https://www.nanordica.com/lv/ravimus?utm_source=email&utm_medium=cold&utm_content=esmakiri-{{utm_id}}

Ja vēlaties izmēģināt brūču aprūpi ar RavimusVET, vienkārši atbildiet uz šo
e-pastu un mēs nosūtīsim bezmaksas paraugu.

Meelis
Šūnu biologs
Nanordica Medical

Jūsu kontaktinformāciju atradām publiskajā veterinārārstu reģistrā. Ja
nevēlaties saņemt vairāk vēstuļu, atbildiet uz šo e-pastu.
```

**Märkused:**
- `Cienījamais` (mees) / `Cienījamā` (naine) — rikastamine valib soo järgi
- UTM `utm_content=esmakiri-{{utm_id}}` — outreach-writer genereerib `utm_id` per deal
- Sotsiaalne tõestus: Pet City ja Evidensia — vähemalt üks arst kummastki testinud ja rahul
- Kliiniline uuring: inimeste peal (DPČ), 30 patsienti, 1 nädal — vt `product-ravimus-vet.md`
- CTA: vastus kirjale → inbox-triage märgib Engaged → outreach-writer saadab kupongi

---

## K2 — järelkiri: kutse akadeemiasse panustada (kinnitatud mall, 2026-07-28)

**Pealkiri:** Uzaicinājums dalīties ar savu pieredzi Brūču aprūpes akadēmijā

**Saatja:** Meelis, Nanordica Medical

**Avarea variandid (rikastamine valib):**

| Stsenaarium | Tekst |
|---|---|
| Kirurgia | {{klīnika}} ķirurģijas prakse nozīmē, ka Jums ir pēcoperācijas brūču aprūpes pieredze, kas varētu būt noderīga citiem ārstiem. |
| Pikaajaline kogemus | Kā ilggadējs praktizējošs ārsts Jums, visticamāk, ir brūču aprūpes metodes, kas ir vērtas uzmanības. |
| Kliinikuomanik | Kā klīnikas īpašnieks Jums, visticamāk, ir praktiski risinājumi, kas gadu gaitā ir izveidojušies un ko citi ārsti varētu arī zināt. |
| Kassid / hobused (mitte koerad) | {{klīnika}} nodarbojas ar {{dzīvnieku sugu}}, kuriem brūču aprūpe bieži ir sarežģītāka — tieši šāda pieredze akadēmijā ir maz pārstāvēta. |

**Kirja tekst:**

```
Cienījamais/ā Dr. {{uzvārds}},

{{personalizēta rinda}}

Brūču aprūpes akadēmijas videomateriāli ir veidoti no praktizējošu
veterinārārstu pieredzes. Ja Jums ir brūču aprūpes metode, ko varētu
izmantot arī citi ārsti, labprāt palīdzēsim to padarīt pieejamu citiem
veterinārārstiem.

Jūs filmējat ārstniecisko paņēmienu ar tālruni — mēs no tā izveidosim
aptuveni vienu minūti garu mācību video ar skaidrojumiem. Jūsu vārds un
klīnika tiks norādīti, pēc vēlēšanās pievienosim arī Jūsu fotoattēlu.
Pirms publicēšanas lūgsim Jūsu galīgo apstiprinājumu.

Šāda video piemērs: https://www.nanordica.com/lv/ravimus?utm_source=email&utm_medium=cold&utm_content=k2-{{utm_id}}

Ja vēlaties video izmantot RavimusVET brūču pārsējus, nosūtīsim tos bez
maksas. Ja Jums ir jautājumi, esmu gatavs arī īsai videokonferencei.

Ko Jūs domājat?

Ar labiem vēlējumiem,
Meelis
Nanordica Medical

Jūsu kontaktinformāciju atradām publiskajā veterinārārstu reģistrā. Ja
nevēlaties saņemt vairāk vēstuļu, atbildiet uz šo e-pastu.
```

**Märkused:**
- `Cienījamais` (mees) / `Cienījamā` (naine) — rikastamine valib soo järgi
- UTM `utm_content=k2-{{utm_id}}` — sama `utm_id` mis K1-s, nurk erineb
- Käivitub +7 päeva pärast K1-t kui vastust pole
- CTA: vastus kirjale → inbox-triage märgib Engaged → outreach-writer saadab K4 (aadressi küsimine)
- Kassid/hobused avarea: mitte kasutada koerte puhul

---

## K3 — breakup-kiri: akadeemia küsib arvamust (kinnitatud mall, 2026-07-28)

**Pealkiri:** Brūču aprūpes akadēmija ir ieinteresēta Jūsu viedoklī

**Saatja:** Meelis, Nanordica Medical

**Kirja tekst:**

```
Cienījamais/ā Dr. {{uzvārds}},

Rakstīju Jums divas reizes par Brūču aprūpes akadēmiju un iespēju tajā
iesaistīties. Jūs neatbildējāt, kas ir pilnīgi saprotami. Varbūt mans
pieejas veids nebija pareizs.

Tomēr, ja Jums kādreiz rodas interese par RavimusVET vai vēlaties
iesaistīties akadēmijā — esmu pieejams. Tāpat varat man laipni paziņot,
kas būtu padarījis šo vēstuļu tēmu Jums interesantu?

Ar labiem vēlējumiem,
Meelis
Nanordica Medical

Jūsu kontaktinformāciju atradām publiskajā veterinārārstu reģistrā. Ja
nevēlaties saņemt vairāk vēstuļu, atbildiet uz šo e-pastu.
```

**Märkused:**
- `Cienījamais` (mees) / `Cienījamā` (naine) — rikastamine valib soo järgi
- Käivitub +14 päeva pärast K1-t (+7p pärast K2-t) kui vastust pole
- Ei ole personaalset avarea ega UTM-linki — tahtlik, hoiab ausa tooni
- Vastus → inbox-triage märgib Engaged → outreach-writer saadab K4
- Vaikus → Lost (no-reply)

---

## K6 — tagasiside-küsimus: näidis kohal (kinnitatud mall, 2026-07-29)

**Pealkiri:** RavimusVet tagasiside

**Saatja:** Meelis, Nanordica Medical

**Kirja tekst (eesti algtekst):**

```
Lugupeetud Dr. {{perekonnanimi}} / {{eesnimi}},

Tasuta RavimusVET haavasidemed on nüüdseks Teieni jõudnud.

Olge hea ja andke mulle teada, millal võiksime oodata esimesi
tulemusi. Eelistatult ootame lühikesi videoklippe haavaravi
metoodikatest, mida saaksime haavaravi akadeemia kaudu teiste
veterinaaridega jagada.

Teie hinnang aitab meil muuta haavasidumise veterinaarias sama
tavapäraseks, kui see on inimmeditsiinis.

Heade soovidega,
Meelis
Nanordica Medical
```

**Läti tekst (language-checker läbinud 2026-07-29):**

```
Cienījamais/ā Dr. {{uzvārds}} / {{vārds}},

Bezmaksas RavimusVET brūču pārsēji tagad ir nonākuši līdz Jums.

Lūdzu, dodiet man ziņu, kad mēs varētu gaidīt pirmos rezultātus.
Vislabāk gaidītu īsus videoklipus par brūču aprūpes metodēm, kurus
varētu rādīt citiem veterinārārstiem Brūču aprūpes akadēmijā.

Jūsu vērtējums palīdzēs mums padarīt brūču pārsiešanu veterinārijā
tikpat ierastu, kā tā ir cilvēku medicīnā.

Ar labiem vēlējumiem,
Meelis
Nanordica Medical
```

**Märkused:**
- Tervitus: kui vet arst vastas eelnevalt eesnimega → `{{vārds}}`; muidu
  `Cienījamais/ā Dr. {{uzvārds}}` (rikastamine valib soo järgi mees/naine)
- **Eesmärk 1:** kinnitab, et tasuta näidis on kohal → tekitab pehme
  vastastikkuse kohustuse (kingitus, mitte arve)
- **Eesmärk 2:** kogub ajastuse signaali ("millal esimesed tulemused") →
  outreach-writer saadab K7 (päris tagasisideküsimus) õigel hetkel
- **Eesmärk 3:** ütleb ette eelistatud tagasisidevormi — lühikesed
  videoklipid haavaravi metoodikatest akadeemia jaoks. Vet peab seda ette
  teadma; nõusolek + nime/kliiniku külgejäämine täpsustatakse K7-s
- Videoklipi-lause: eesti "jagada" (dalīties) annaks kohmaka topelt-"ar",
  seepärast läti tekstis `rādīt` (näidata) — akadeemia kontekstis sama mõte
- Opt-out rida puudub (kontakt on Engaged, suhe aktiivne)
- Käivitub **+1 päev** pärast S5 (Näidis kohal) kinnitust
- Tootenimi kirjades: alati `RavimusVET` (läti kasutusjuhendis on
  `RAVIMUS VET`, aga turunduses hoiame ühtset `RavimusVET`)
- QA: `nu`→`tagad`, `pie Jums`→`līdz Jums` (language-checker); allkiri
  `Ar labiem vēlējumiem` ja `dodiet ziņu` hoitud K2/K3 kooskõla + soe toon

---

## Vana näidiskiri 1: esmane pöördumine, kassiarst (lv mustand, asendatud)

> **Pealkiri:** {{eesnimi}}, atraumatiska pārsiešana kaķiem?
>
> Labdien, {{eesnimi}}!
>
> Redzēju, ka {{kliinik}} piedāvā ķirurģiju un pēcoperācijas brūču aprūpi.
>
> Esmu Karmen no Nanordica. Izstrādājām RavimusVET, sterilu brūču pārsēju ar
> zīda nanošķiedru un sudraba un vara nanodaļiņām. Klīniskā pētījumā brūces
> dzija gandrīz divreiz ātrāk nekā ar sudraba pārsējiem, un pārsēja maiņa ir
> atraumatiska, kas nozīmē mazāk stresa nemierīgam kaķim.
>
> Apskatiet RavimusVET tuvāk šeit → [tooteleht + UTM]
>
> Ar cieņu,
> Karmen, Nanordica
>
> _Jūsu kontaktu atradām publiskajā veterinārārstu reģistrā._
> _Ja nevēlaties no manis vairāk saņemt vēstules, dodiet ziņu, atbildot uz šo e-pastu._

CTA on **kindel ja käskiv** ("Apskatiet ... šeit"), mitte küsiv. Loobumine on
**selge, sõbralik rida kirja kõige lõpus**, allkirja järel, CTA-st eraldi
(`cold-outreach.md`).

CTA-link tuleb märgistada UTM-iga (`funnel-framework.md`).

## Töövoog kirja koostamisel

1. Vaata kontakti staatust ja saadetud kirjade arvu.
2. Vali järgmine nurk pangast (ära korda eelmist).
3. Leia värske haak (`contact-enrichment.md`).
4. Kirjuta läti tekst, personaliseeri loomaliigi järgi.
5. Lisa UTM-link, opt-out, nimeline saatja.
6. **Läbi automaatne QA värav** (`latvian-qa.md`): korrektuur + tagasitõlge +
   väite-kontroll. Alles siis märgi valmis.
7. Anna ka kohatäidetega versioon mail-merge tööriista jaoks.
