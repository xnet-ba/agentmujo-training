# Split freeze (2026-09-22) — train/valid/test zamrznuti

Metoda: `amj dataset split` (hash ID-a mod 100: <80 train, <90 valid,
ostalo test). Deterministički — ponovljivo iz kanonskih fajlova.

| Skup | Train | Valid | Test | Ukupno |
|---|---|---|---|---|
| function-calling | 929 | 121 | 132 | 1182 |
| agentic-terminal | 450 | 42 | 49 | 541 |
| bosnian-core | 796 | 118 | 86 | 1000 |

Fajlovi: `datasets/splits/{fc,ag,bc}/{train,valid,test}.jsonl`
(leže u gitu — mali su — i na HF Hubu u istim dataset repoima pod `splits/`).

## Leakage izvještaj (`datasets/splits/leakage_report.json`)

- ID-evi disjunktni po splitovima: DA (testirano u CI, `test_leakage.py`).
- Content-hash duplikati: NEMA.
- Bench izolacija: v0.5 prompti se **doslovno ne preklapaju** sa treningom
  (`bench_isolated: true`). Serije 30/31 su imale 5+8 literalnih preklopa —
  uhvaćeno leakage provjerom i preformulisano prije mergea (procesna disciplina).
- v0.1–v0.4 bench fajlovi su zamrznuta historija, ne koriste se za trening.

## Pravilo

Novi uzorci dobijaju split istom metodom; freeze se ponavlja
samo uz novi leakage izvještaj i bump verzije splitova.
