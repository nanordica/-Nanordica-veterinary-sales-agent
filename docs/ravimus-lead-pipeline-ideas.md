# Ravimus lead-pipeline — multi-agent süsteemi ideed

*Seis: 2026-06-12. Brainstormi vahekokkuvõte — arhitektuurivalik on veel
lahtine (soovitus: variant A).*

## Ülesanne

Multi-agent süsteem, mis viib ühe lead'i avastamisest esimese müügini.
Agendid leiavad prospekti, rikastavad ja kvalifitseerivad selle ning
suhtlevad lead'iga otse — saadavad igas staadiumis õige sõnumi ja
nügivad lead'i samm-sammult müügitorus suletud müügi suunas.

- **Sihtgrupp:** Läti veterinaararstid (riiklikust registrist), eesmärk
  on jaeost.
- **Toode:** Ravimus haavaside (Nanordica).

## Tehtud otsused

| Küsimus | Otsus |
|---|---|
| Olemasolev taristu | Pipedrive konto + API token; Wixi pood live; e-posti ligipääs olemas; vetiregistri andmed laeme ise alla |
| Autonoomsus | Täisautonoomne — agendid saadavad kirju ilma inimkinnituseta |
| Runtime | Claude Code agendid + cron |
| Maht | Väike partii, ~5–20 vetti korraga pipeline'is |
| Kirjade keel | Läti keel |
| E-posti ligipääs | Microsoft 365 (enterprise) — Graph API saatmiseks ja vastuste lugemiseks; tokenid antakse hiljem |

## Tööriistad agentidele

1. **E-post** — ravimus@nanordica.com, Microsoft Graph API kaudu
   (saatmine + vastuste lugemine).
2. **Pipedrive** — müügitoru haldus; iga lead on deal, staadium = lead'i
   olek pipeline'is.
3. **Wix** — veebipood müügi teostamiseks; ost on pipeline'i lõppsignaal.

## Arhitektuurivariandid

Runtime on otsustatud (Claude Code + cron); valik on selles, kuidas
agendid ja olek struktureerida.

### A) Üks orkestraator-tikk + subagendid, Pipedrive ainsa tõeallikana — SOOVITUS

Cron käivitab regulaarselt (nt iga 30 min) ühe Claude Code sessiooni
("pipeline tick"). Tikk:

1. loeb Pipedrive'ist kõik deal'id ja nende staadiumid;
2. otsustab iga lead'i kohta järgmise sammu;
3. delegeerib töö spetsialiseeritud subagentidele:
   - **discovery** — leiab registrist uued vetid, loob deal'id;
   - **enrichment** — rikastab kliiniku/kontakti andmed;
   - **qualification** — hindab sobivust, diskvalifitseerib sobimatud;
   - **outreach-writer** — koostab lätikeelse kirja vastavalt staadiumile;
   - **inbox-triage** — loeb vastused Graphi kaudu, liigutab staadiumi.

Kogu olek elab Pipedrive'is — kui tikk katkeb, jätkab järgmine sealt,
kus asjad pooleli jäid.

**Plussid:** lihtne, taaskäivitatav, iga komponent eraldi testitav,
demo'tav ühe käsuga. **Miinused:** kõik sammud jagavad üht ajakava
(tiki sagedus määrab reaktsioonikiiruse).

### B) Iga agent eraldi cron-rutiin

Discovery jookseb hommikuti, enrichment iga tund, outreach kaks korda
päevas, inbox-triage iga 15 min — igaüks loeb Pipedrive'ist oma
staadiumi lead'id.

**Plussid:** agendid on sõltumatud, igal oma rütm; "päris" multi-agent
tunne. **Miinused:** 4–5 eraldi ajastatud protsessi — rohkem seadistust
ja logimist, race-tingimuste risk (kaks rutiini puudutavad sama
lead'i).

### C) Agent team — pidev mitme agendi sessioon

`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` on juba sisse lülitatud: üks
pikalt elav tiimisessioon, kus discovery-, outreach- ja inbox-agendid
suhtlevad omavahel sõnumitega.

**Plussid:** efektne demo. **Miinused:** eksperimentaalne, raskem
taaskäivitada, häkatoni ajaraamis riskantne.

### Soovituse põhjendus

A annab sama "agendid leiavad, kvalifitseerivad, suhtlevad" loo, aga
oleku hoidmine Pipedrive'is teeb süsteemi vastupidavaks ja iga
komponent on eraldi testitav. B-le saab hiljem üle minna lihtsalt
cron-e juurde lisades — tiki sisu ei muutu.

## Lahtised küsimused

- Pipedrive'i staadiumite täpne loetelu (eskiis: Discovered → Enriched
  → Qualified → Contacted → Engaged → Won/Lost).
- Wixi ostu tuvastus: webhook vs Orders API pollimine; ostja e-posti
  sidumine deal'iga.
- Microsoft Graphi tokenite hankimine ja õigused (Mail.Send,
  Mail.Read).
- Läti vetiregistri täpne allikas ja allalaadimisformaat.
- Follow-up rütm ja loobumisreeglid (mitu kirja enne Lost-staadiumi;
  opt-out käsitlus).
