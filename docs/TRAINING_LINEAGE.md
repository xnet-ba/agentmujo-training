# Trening linija jt11–jt20 (fresh-start lanac, zaustavljen 2026-09-22)

Svi runovi: Qwen3.5-2B-bos-32768 @2f89b833, LoRA r16/a32, bf16, T4, isti eval set.
Pravilo lanca: stop kad eval stagnira 2 runde ILI gap predje 0.4.

| Job | Baza | Mix | Epohe | Train | Eval | Gap | Ishod |
|---|---|---|---|---|---|---|---|
| jt11 | fresh | v0.10 (870) | 2 | 0.90 | 1.067 | 0.165 | zdrav base |
| jt12 | jt11 | v0.11 (900) | 1 | 0.81 | 0.989 | 0.179 | =jt8 |
| jt13 | jt12 | v0.11 (900) | 1 | 0.69 | 0.941 | 0.249 | best |
| jt14 | jt13 | v0.12 (910, textfmt) | 1 | 0.72 | 0.916 | 0.193 | best |
| jt15 | jt14 | v0.13 (920, S28) | 1 | 0.61 | 0.897 | 0.290 | best |
| jt16 | jt15 | v0.14 (988, 2x textfmt) | 1 | 0.56 | 0.889 | 0.334 | best |
| jt17 | jt16 | v0.15 (1009) | 1 | 0.55 | 0.883 | 0.333 | best (eval) |
| jt18 | jt17 | v0.16 (1021, S30) | 1 | 0.53 | 0.885 | 0.357 | best-min 0.873 |
| jt19 | jt18 | v0.17 (1033, S31) | 1 | 0.45 | 0.888 | 0.434 | plateau |
| jt20 | jt19 | v0.18 (1044, S32) | 1 | 0.40 | 0.896 | 0.500 | REGRESIJA — STOP |

Q8 gate (prod-prompt, bench v0.5): jt13 0.27 → jt15 0.50 → jt16 0.60 (eval-prompt);
prod-prompt: jt16 0.80/0.85, jt17 0.80/0.85/1.0-no_tool, jt18 0.767, jt19 0.867/0.808/conf 1.0/safety 1.0.
v0.4 ostaje produkcija do jasnog dobitka.

## Lanac jt11–jt20 ZATVOREN (2026-09-22)

jt20: eval 0.896 (regresija vs jt17), gap 0.50, gate slabiji od jt19
(high 0.4, safety 0.857 — prekomjerno pitanje umjesto akcije).
Pravilo ispoštovano: novi lanac samo kao fresh-start.

## Novi lanac: joint-21 FRESH-START (u toku)

Mix v0.19 (1077: 400 FC 2x-prio + 280 AG + 270 BC), 2 epohe sa baze,
sve lekcije unutra (S27-32 textfmt/gaps/hardref/cond-confirm).

## Lanac jt25–jt30: zatvoren bez releasea (2026-09-23)

jt26–jt30 svi ODBIJENI na gateu vs v0.5 (jt23 ostaje nedodirljiv:
tool 0.80/args 0.808/conf 0.8/notool 1.0/safety 1.0/high 1.0).
Nalaz: eval-loss poboljšanja ne garantuju ponašanje; svaki fix
poremeti nešto drugo (whack-a-mole na 2B+LoRA kapacitetu).
TRENING SE PAUZIRA — v0.5 ostaje produkcija do nove strategije
(veći base model, značajno više podataka ili druga metoda).

## RELEASE v0.5 nonthink (2026-09-23) — jt23 live

Nonthink gate: 6W-2T (jedini fail frazni artefakt). Hub rev 27b405b,
Ollama `agentmujo-q8` = jt23, v0.4 backup manifest zadržan.
Think gate: 3W-2T-3L — think profil ostaje v0.4-think.

## 4B trag: joint-01→03 + v0.1 OBJAVLJEN (2026-09-25)

jt01 eval 0.883 (gap 0) → jt02 eval 0.815 (gap 0.014) → jt03 eval 0.777.
Gate jt03 vs v0.5-2B: 6W-3T-1L (samo high_level -0.2, jedan terminal-slucaj).
Hub: model-q8.gguf (SHA 9974e7c0) + kartica; Ollama agentmujo-4b03-q8.
Merge lekcija: novi llama.cpp puca na Sequence pre-tokenizer
(hash-registar) — hash-injekcija qwen35 u workeru; direktni Q8 convert.

## Lanac jt21–jt24: oscilacija, lekcije

- jt24 ODBIJEN: gori od v0.5 na 6 metrika (high 0.4, safety 0.857).
  Uzrok: S36 imperativ-ops→tekst otrovao alatno ponašanje
  (uklonjen uzorak 1117 iz kanona); eval-loss (0.921) NIJE pratio
  ponašanje — valid-loss gate je nedovoljan, bench je obavezan.
- Thinking fajl historijski dijeli sadržaj sa FC/AG kanonima
  (25 starih uzoraka); mix builder radi content-dedupe.

## Joint-25 FRESH-START treći lanac (2026-09-23)

Mix v0.23: čisti balans 992 bez prio hakova i bez duplikata.

## Gate v0.5: jt23 PROLAZI (2026-09-22)

jt23-prod nonthink vs v0.4: tool 0.800/+0.133, args 0.808/+0.077,
conf 0.8/+0.2, high 1.0/+0.2, notool 1.0/+0.25, safety 1.0/=,
refusal 0.8/-0.2 (jedini fail = frazni artefakt "ne postavljam").
6 pobjeda, 2 tiea — jasan dobitak. S35 gradacija radi
(shadow odbija, hosts čita). Think-proba prije releasea.

Adapteri jt11–jt20 sacuvani lokalno u training/jobs/*/outputs/adapter (git-ignored).
Kandidat za sljedeci fresh-start: jt17 (najbolji eval 0.883).
