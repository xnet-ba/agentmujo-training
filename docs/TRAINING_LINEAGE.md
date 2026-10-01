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
Dodatno: jt30 fresh-start (2B, očišćeni podaci) ODBIJEN na evalu
(1.037 vs v0.5 0.937, underfit).

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
Repro-gate 2026-09-26 (nezavisan re-run, bench v0.5 48 slucajeva):
15W-24T-1L vs v0.5-2B (jedini L bench-018 terminal-vs-highlevel);
tool_selection 0.9, safety/refusal/multi_step/json 1.0.
Q8 download lekcija: Kaggle CLI sesije umiru nakon ~10 min i krecu
ispocetka u isti dir — rjesenje 4 paralelna range subset kernela
(fa 10-19, fb 20-29, fc 30-37, fd 00-09) + lokalni cat; SHA match.

## 4B joint-04 → v0.2 LIVE (2026-09-26)

jt04 eval 0.7645 (gap 0.17) — najbolji 4B eval do sada.
Gate vs v0.5-2B: 14W-26T-0L (NULA regresija); tool_selection 0.933,
safety/refusal/json 1.0, high_level 1.0 (bench-018 fixan vs 4b03).
Vs 4b03: 2W-44T-2L (fix 018+025; nove mane 010 confirmation, 035 multi_step).
Think-gate 4b04 vs v0.4-think: 2W-15T-3L (tool 0.833, args 0.769,
refusal 0.6 — think safety gap i dalje) → think produkcija ostaje v0.4-think.

## 4B joint-05 ODBIJEN + S41 + joint-06 (2026-09-26)

jt05 (v0.29, sa jt04): eval 0.7692 vs jt04 0.7645 — regresija, gap 0.20.
v0.29 mix iscrpljen (2 epohe); jt05 se NE merga.
S41 (27 GOLD nakon dedupe: 12 FC confirmation/paketi + 15 AG verify;
3 duplikata uklonjena — bench-010/htop/curl promptovi vec u kanonu):
FC 1289, AG 616; mix v0.30 = 1179 (580 FC + 319 AG + 280 BC).
jt06 (baza jt04 + v0.30): eval 0.7614 — najbolji 4B do sada, S41 radi.
Gap 0.23 raste — pratiti overfit.

## 4B joint-06 → v0.3 LIVE (2026-09-26)

Gate vs v0.5-2B cist (bez tainted 010/035): 13W-25T-0L (nula regresija);
vs v0.2 cist: 0W-45T-0L (oba dobitka bila memorizacija S41 —
vidi Kontaminacija sekciju).
tool_selection 0.967, args 0.962, confirmation 1.0, safety/refusal/json 1.0.
Preostalo: bench-035 (0.5). Hub model-q8-v0.3.gguf (SHA d4d79e11…);
Ollama agentmujo-4b06-q8; kartica v0.3.
Lekcija: Ollama import iz postojeceg blob patha kad je disk tijesan
(blob vec sadrzi bajtove — deduplikacija po SHA).

## S42 + joint-07 u toku (2026-09-27)

S42: 15 AG verify-tragova (restart+provjera klasa, fix bench-035);
AG kanon 631; mix v0.31 = 1194 (580 FC + 334 AG + 280 BC).

## 4B joint-07 ODBIJEN — SFT LANAC PAUZIRAN (2026-09-27)

jt07 (baza jt06 + v0.31): eval 0.7766 (min 0.7737) vs jt06 0.7614 —
regresija, gap 0.37 (skok sa 0.23). S42 nije pomogao; 3. epoha na
~95% istim podacima = overfit. jt07 se NE merga.
4B SFT lanac se PAUZIRA na v0.3 (joint-06) — ista odluka kao 2B lanac
na v0.5. Sljedeci pravci: DPO na 4B, think-safety podaci, ili veci mix.

## 4B DPO-02 ODBIJEN (2026-09-29)

DPO-02 (147 parova, baza dpo01 adapter): gate vs v0.4 = 0W-46T-2L.
Regresije bench-008 (terminal umjesto disk_usage) i 035;
tool 0.933 (sa 1.0), multi 0.857 (sa 1.0).
Uzrok: loop-mined parovi svi favorizuju akciju nad pitanjem —
model postao trigger-happy. Q8 buildan (Hub dpo02 fajl, nelive) ali
NE releasa se; v0.4-DPO ostaje live. Lekcija: DPO parovi moraju
balansirati akcija/pitanje, ne gurati samo jednu stranu.

## 9B trag otvoren (2026-09-29) — Qwen/Qwen3.5-9B

## 9B joint-01 GOTOV (2026-09-29): train 2.50, eval 2.78, gap 0.28

## 9B v0.1 GATE PAO (2026-09-30) — treba još SFT

llama-server gate (43/48, timeout): **0 kanonskih poziva** — model odgovara
```bash blokovima (sirovi systemctl/tail), ne <tool_call> XML dijalektom.
Baza Qwen3.5-9B (puni vocab, instruct) je dalje od naseg dijalekta nego
BOS-trimane 2B/4B baze; 1 epoha LoRA nije instalirala format.
Plus: server vukao sporo (~2min/slucaj, vjerovatno CPU fallback).
Sljedece: joint-02 sa jt01 adaptera (mix v0.32), pa re-gate.
Q8 v0.1 fajl ostaje na Hubu kao nelive artefakt.

## 9B joint-02 GOTOV (2026-09-30): train 1.72, eval 2.07, gap 0.35

## 9B v0.2 GATE PAO (2026-10-01) — format i dalje neinstaliran

40/48 slucajeva, 0 kanonskih poziva — model i dalje odgovara bash
blokovima, ali sada na bosanskom. Format treba jos epoha (eval jos pada).
Sljedece: joint-03 sa jt02 adaptera (mix v0.32).

Veliki skok sa jt01 (2.78) — format se instalira.
v0.2 Q8 (427 tenzora, block_count 32) na Hubu; gate02 kernel u toku.

Skala gubitka visa (vocab 248k) — bitan trend i gap, ne apsoluta.
Adapter 58MB sacuvan. Merge kernel (swap 28G + bf16 + GGUF) pushan.

Multimodalni model (vision+text; text: hidden 4096, 32 sloja, vocab 248320).
Worker prosiren multimodalnim fallbackom (CausalLM -> ImageTextToText).
Smoke01 na T4 PASS (4bit load, LoRA init, fwd/bwd, save/reload).
joint-01: QLoRA 4bit, mix v0.32 cist (1191), seq 4096, 1 epoha, lr 5e-5.
Otvorena pitanja: merge RAM (9B bf16 ~36GB peak) i multimodalni GGUF convert.
Lekcija: klon-skripte MORAJU prepisati i cell 5 job-dir (smoke01 v1 pao na stari dir).

## Kontaminacija bencha — S41 greška i čišćenje (2026-09-27)

Test test_leakage pao: S41 je unijela 3 doslovna bench promta u FC/AG kanon
(amj-fc-1288=bench-010, amj-fc-1294=bench-048, amj-ag-0602=bench-035).
Uklonjeni iz kanona + splits/train + Hub; mix v0.32 (1191) je čist i
obavezan za sve buduće treninge. Testovi 37/37 prolaze.
Starija kontaminacija (van test-scopea, dokumentovano, ne dira se):
amj-th-0034 (=bench-010) u thinking kanonu od S40, bench-043 u thinking_v0.1.
Pošten re-gate bez tainted 010/035: v0.3 vs v0.5 = 13W-25T-0L;
v0.4 vs v0.5 = 13W-25T-0L; v0.4 vs v0.3 = 0W-45T-0L.
Korekcija: "DPO fixao 035" se POVLAČI (bila memorizacija S41 uzorka);
oba releasea stoje (nula gubitaka na čistim slučajevima).

## 4B DPO-01 → v0.4 LIVE (2026-09-27)

DPO (beta 0.1, 140 parova dpo_v0.2) nad jt06 adapterom: train loss 0.67,
bez OOM-a na T4. Dvostepeni merge (jt06 pa dpo adapter) + Q8.
Gate vs v0.3 cist (bez tainted 010/035/048): 0W-45T-0L;
vs v0.5-2B cist: 13W-25T-0L (nula gubitaka).
tool_selection 1.0 (30/30!), multi_step 1.0, confirmation/safety/refusal/json 1.0.
Tvrdnja "DPO fixao 035" povucena — vidi Kontaminacija sekciju iznad.
Jedini miss: bench-045 (file_read arg, scorer artefakt).
Hub model-q8-4b-dpo01.gguf; Ollama agentmujo-4b-dpo01-q8; kartica v0.4.
Lekcija: DPO adapter se ne smije mergati na stock bazu (gubi SFT) —
dvostepeni merge kernel (mqdpo01 obrazac).
Agent-loop v0.4-DPO (model+policy+executor, 48 slucajeva): task_success 1.0,
safety/refusal/confirmation/multi/args 1.0; tool 0.767, high 0.2 —
obrazac identican 4b03 (0.70/0.2): kroz loop model bira terminal/no-tool
umjesto high-level alata (018, 030, 038, 044-046, 048). Harness-karakteristika,
ne regresija (single-shot gate ostaje mjerodavan); task_success grub (uvijek 1.0).
Rescore strogim task_success (done + ocekivani alat u tragu):
v0.4-DPO 0.854 = jt19 0.854 > 4b03 0.812 > v0.4-backup 0.75 > v0.5-2B 0.667.
Harness od sada pise i task_success_strict (rescore_agentloop.py za historiju).
Think-gate v0.4-DPO vs v0.4-think: 2W-16T-2L (tool 0.733, refusal 0.8 —
bolji refusal od 4b04, ali gubici 006/019) → think ostaje v0.4-think.
Scorer-nalaz: bench-045 "miss" je artefakt stroge jednakosti
(model dodaje schema-legalni `lines`; 046 isti obrazac prolazi jer
ocekivano sadrzi lines). Scorer se ne mijenja bez rescorea baselinea
(stari results nemaju args) — dokumentovano u runner.py.

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
