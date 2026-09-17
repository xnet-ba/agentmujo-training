# Bosanska proba baze (2026-09-15) — odluka o bosnian-core skupu

Proba: `benchmark/bosnian_probe.py`, 12 promptova, profil `q8-nonthink`
(Q8 baza, temperature 0.7). Automatika: 12/12 non-empty, 10/12 bez
ekavizama. Slijedi ručna ocjena svakog odgovora
(`benchmark/results_bosnian_probe.json`).

## Ručna ocjena

| ID | Prompt | Jezik (ijekavica) | Sadržaj | Ocjena |
|---|---|---|---|---|
| bp-01 | fotosinteza | OK | izmišljotine ("klora", "plavi hlorofil") | jezik DA / znanje NE |
| bp-02 | čestitka | OK ("Sretno ti rođendan" neprirodno) | prihvatljivo | djelimično |
| bp-03 | vrijeme/vrijednost | OK ("vreme" bio lažni pogodak na "vremena" — ispravljeno na granice riječi) | brbljanje, "Time/Gear time" besmislica | jezik DA / znanje NE |
| bp-04 | prevod server | savršeno | tačno ("Serveru treba više memorije.") | DA |
| bp-05 | internet djetetu | slabo ("svetu", "računar") | konfuzna metafora bazena | NE |
| bp-06 | mlijeko | propust ("svežom" umjesto "svježom") + gramatička greška | slabo | NE |
| bp-07 | džep | površina OK | **potpuno pogrešna definicija** (džep = "dno vode"?) | NE |
| bp-08 | prognoza | OK | kontradikcija (30°C + "jaka odjeća") | djelimično |
| bp-09 | da li / je li | OK | konfuzno ("pravna funkcija") | NE |
| bp-10 | sažetak Linux | savršeno | tačan sažetak u jednoj rečenici | DA |
| bp-11 | padež "kuću" | OK | **pogrešno** ("diktalni padež" ne postoji; tačno: akuzativ), samouvjereno | NE |
| bp-12 | kuhanje kafe | NE ("Kuvanje", "kuva") + besmislen recept | NE | NE |

## Re-proba na fine-tuniranom modelu (v0.2, 2026-09-17) — FORGETTING

Isti 12 promptova na `agentmujo-q8` (Q8 think-adapter merge).
Automatika: 12/12 non-empty, no_ekavian 0.58–0.75 (uzorak šuma na temp 0.7).

Ručna ocjena (poređenje sa bazom):

- bp-01: "gde" (ekavizam!), sadržaj slabiji nego baza.
- bp-02 (čestitka): "Dobrodošao, rodilac, novorođenčadi!" — besmislica.
- bp-04 (prevod): **odbija prevesti** ("Prevođenjem ne mogu riješiti nulti problem") —
  over-refusal prenesen iz safety treninga na benigni zahtjev.
- bp-05/12: **forsira tool pozive** u brbljanje (`doc_provide` halucinirani alat,
  `service_status(coffee-maker)`).
- bp-06: "Mlijeko je klasičan izvor zla" — besmislica.
- bp-11: "padež je obješen" — besmislica (baza je bar griješila samouvjereno).

## Revidirana preporuka: bosnian-core je sada POTREBAN

Uski tool SFT izazvao je **katastrofalno zaboravljanje općeg bosanskog**:
tečnost izvan distribucije alata je uništena, a refusal se prelijeva na
benigne zahtjeve. Odluka o odgodi se POVLAČI. Sljedeće:

1. `agentmujo-bosnian-core`: opći razgovor, znanje, gramatika, prijevodi
   (nekoliko stotina uzoraka, bez alata).
2. Joint re-trening sa bosnian-core udjelom (replay protiv forgettinga).
3. Re-proba: cilj vratiti tečnost uz zadržane tool metrike.

1. **Operativni bosanski radi:** kratki prevodi, sažeci i statusne
   poruke (bp-04, bp-10) su tačni i čista ijekavica. To je 90% onoga što
   AgentMujo agent treba (statusi, potvrde, verifikacije).
2. **Znanje i objašnjavanje su slabi:** halucinirane definicije (džep,
   padeži), konfuzna objašnjenja, povremeni ekavski propusti
   (svežom, svetu, kuvanje) i samouvjerene greške.
3. Heuristika je pooštrena: granice riječi (lažni "vreme"⊂"vremena"
   eliminiran) + 13 novih markera (gde/ovde/čovek/posle/kuvati...).

## Preporuka (2026-09-15, HISTORIJSKA — povučena 2026-09-17): bosnian-core ODGOĐEN

> Ova odluka je vrijedila za BAZU. Re-proba na fine-tuniranom modelu
> (vidi gore) pokazala je catastrophic forgetting — odluka se POVLAČI,
> bosnian-core postaje obavezan (vidi "Revidirana preporuka").

Poseban jezički skup se NE pravi. Umjesto toga:

- Svi dataset uzorci i dalje nose finalne odgovore na **uzornoj ijekavici**
  (pozitivan transfer kroz SFT, bez posebnog skupa).
- Objašnjavajući stil se u agent datasetima izbjegava — agent daje
  kratke operativne poruke, ne eseje.
- `bosnian_quality` u benchu ostaje manual/LLM-sudija kategorija;
  `ijekavica_dialect` heuristika je automatski regresioni čuvar.
- Re-evaluacija tek ako fine-tunirani model pokaže jezičku degradaciju
  (catastrophic forgetting) na operativnim porukama.
