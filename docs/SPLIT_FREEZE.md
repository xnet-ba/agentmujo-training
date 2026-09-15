# Split freeze (2026-09-15) — train/valid/test zamrznuti

Metoda: `amj dataset split` (hash ID-a mod 100: <80 train, <90 valid,
ostalo test). Deterministički — ponovljivo iz kanonskih fajlova.

| Skup | Train | Valid | Test | Ukupno |
|---|---|---|---|---|
| function-calling | 99 | 16 | 12 | 127 |
| agentic-terminal | 88 | 8 | 9 | 105 |

Fajlovi: `datasets/splits/{fc,ag}/{train,valid,test}.jsonl`
(leže u gitu — mali su — i na HF Hubu u istim dataset repoima pod `splits/`).

## Leakage izvještaj (`datasets/splits/leakage_report.json`)

- ID-evi disjunktni po splitovima: DA (testirano u CI, `test_leakage.py`).
- Content-hash duplikati: NEMA.
- Bench izolacija: v0.3 prompti se **doslovno ne preklapaju** sa treningom
  (`bench_isolated: true`). v0.2 je imao 9 literalnih preklopa —
  parafrazirano u v0.3 (isti ID-evi i očekivanja, novo ruho).
- v0.1/v0.2 bench fajlovi su zamrznuta historija, ne koriste se za trening.

## Pravilo

Novi uzorci (serija 7+) dobijaju split istom metodom; freeze se ponavlja
samo uz novi leakage izvještaj i bump verzije splitova.
