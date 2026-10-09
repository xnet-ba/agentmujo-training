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

Multimodalni model (vision+text; text: hidden 4096, 32 sloja, vocab 248320).
Worker prosiren multimodalnim fallbackom (CausalLM -> ImageTextToText).
Smoke01 na T4 PASS. Skala gubitka visa (vocab 248k) — bitan trend i gap.
Otvorena pitanja bila: merge RAM (~36GB peak, rijeseno swapom) i multimodalni
GGUF convert (radi). Lekcija: klon-skripte MORAJU prepisati i cell 5 job-dir.

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

Veliki skok sa jt01 (2.78) — format se instalira.
v0.2 Q8 (427 tenzora, block_count 32) na Hubu.

## 9B v0.2 GATE PAO (2026-10-01) — format i dalje neinstaliran

40/48 slucajeva, 0 kanonskih poziva — model i dalje odgovara bash
blokovima, ali sada na bosanskom. Format treba jos epoha (eval jos pada).

## 9B joint-03 GOTOV (2026-10-01): train 1.50, eval 1.89, gap 0.39

Jos pada (2.78→2.07→1.89); gap raste — pratiti.
v0.3 Q8 (427 tenzora) na Hubu.

## 9B v0.3 GATE PAO (2026-10-01) — 0 kanonskih i nakon 3 epohe

46/48, model i dalje bash blokovi. Zakljucak: LoRA ne instalira gramatiku
(strukturno, ne vremensko). Sljedece: 9B DPO-01 sa 27 format parova
(rejected=9B bash, chosen=4B kanonski; dpo_9b_v0.1), 3 epohe.

## 9B DPO-01 GOTOV (2026-10-01): loss 0.67, dvostepeni merge u toku

## 9B DPO Q8 na Hubu (2026-10-04)

DPO Q8 (427 tenzora, ~9.5GB) kao model-q8-9b-dpo01.gguf.
Lekcija: assembly na 92% diska puca na zadnjim chunkovima — prvo
obrisati vec-sastavljene chunk direktorije, truncate fajla na granicu,
pa append ostatka.

## 9B DPO GATE PAO (2026-10-04) — pa nastavak SFT-a

47/48 slucajeva, 0 kanonskih poziva — DPO (27 format parova, 3 epohe)
nije instalirao dijalekt. Medjutim: nema 9B BOS baze (alphaedge ima
samo 0.8B/2B/4B), a eval trend pada (2.78→2.07→1.89) bez overfita —
pa se nastavlja SFT: joint-04 sa jt03 adaptera (mix v0.32).

## 9B joint-04 GOTOV (2026-10-04): train 1.41, eval 1.82, gap 0.40

Jos pada (2.78→2.07→1.89→1.82). Format-proba jt04 (5 promptova,
direktno na adapteru): 0/5 kanonskih — namjera se formira (naracija
o alatima na engleskom), gramatike nema.
ODLUKA: jos jedna r16 epoha (jt05); ako proba i dalje 0/5 → r64 fresh
sa baze (ne trositi vise r16 epoha). Kriterij zaustavljanja eksplicitan.

## 9B joint-05 GOTOV (2026-10-04): train 1.38, eval 1.81, gap 0.43

Eval stagnira (1.82→1.81), gap raste — stop-kriterij aktiviran.
Proba jt05: 0/5 → STOP r16 (5 epoha, format 0).
ODLUKA: r64/alpha128 FRESH sa baze (4x kapacitet); r16 adapteri
nespojivi sa visim rankom. Proba nakon r64-01 odlucuje dalje.

## 9B r64-01 GOTOV (2026-10-04): train 1.71, eval 2.06, gap 0.34

Jedna r64 epoha = eval 2.06 (r16 trebao 3 epohe za 1.89). Bez OOM-a.
Format-proba r64: 0/5. Template provjeren lokalno — render cist
(<tool_call> verbatim, prazan think marker po D1); problem je ucenje.

## 9B r64-02 GOTOV (2026-10-05): train 1.40, eval 1.80, gap 0.40

Velik skok (2.06→1.80). Format-proba r64-02: 0/5.
HIPOTEZA sa mehanizmom: LoRA ne dira embed_tokens/lm_head, a 9B baza
nema nativnu tool semantiku u embeddingima (BOS baze imaju) — gramatika
fizicki ne moze izaci. ODLUKA: r64e-01 FRESH sa embed_tokens+lm_head
u targetima (+~64M LoRA parametara, staje na T4). Ako proba pokaze
format → pipeline; ako 0/5 → 9B pauza (format-spec pristup).
r64e v1 OOM (13.3GB + treba jos 1.65GB). Ispostavilo se: worker ODBACUJE
max_seq_length (nepodrzan TRL kljuc) — seq fix nikad nije primijenjen
(ionako nebitan: mix max 403 tokena). Pravi fix: optim passthrough
u workeru + paged_adamw_8bit za r64e (stednja ~1.5GB na states). v3 pushan.
v3 OOM na koraku 30/38 (+2.28GB fali) — T4 ne moze r64+embed.
ODLUKA: r16h-01 FRESH (r16 + embed/lm_head, +16M param — r16 je dokazano
stao); ista hipoteza, manji otisak. Proba nakon toga odlucuje.

## 9B r16h-01 OOM (2026-10-05)

r16+embed/lm_head takodje OOM (+2.28GB fali; 12.49GB u upotrebi).
Bilans 9B: r16x5 + DPO + r64x2 + r64e + r16h — format 0/5 svuda;
embed put 3x OOM na T4. Pauza po najavljenom kriteriju.

## 9B pivot na v0.33 trening (2026-10-06)

## 9B r64-03 GOTOV (2026-10-06): metrike se vade, proba6403 pushana

## 9B proba r64-03: 0/5 — ali druga epoha v0.33 (2026-10-06)

## 9B v0.4 Q8 na Hubu, gate05 sa spec promptom (2026-10-07)

r6404 merge (v0.33 x2) → Q8 427 tenzora → model-q8-v0.4.gguf na Hubu.
Gate05: LLAMA_BENCH_SYSTEM_FILE=system_spec.txt (prvi gate sa
format-spec protokolom).

## 9B proba r64-04: 0/5 — data-hipoteza mrtva, format-spec protokol (2026-10-06)

Dvije epohe v0.33, i dalje 0 kanonskih pod default promptom.
ODLUKA: format-spec postaje dio 9B protokola (ne dira se 2B/4B);
gate sa spec promptom (LLAMA_BENCH_SYSTEM_FILE) mjeri pravi strop.
Puni pipeline za r6404: merge → Q8 v0.4 → gate05 sa spec.

Proba nakon 1 epohe v0.33: 0/5 (ocekivano slab signal: 11% uzoraka).
ODLUKA: r64-04 (druga epoha v0.33 sa r6403) pa puni gate (merge/Q8/bench)
— posten test data-hipoteze prije suda.

r16eh-01 takodje OOM (ista +2.28GB rupa) — embed put definitivno mrtav
na T4 u svim rankovima. ODLUKA: pivot sa tezina na podatke — r64-03
nastavak sa r6402 adaptera na mixu v0.33 (format-spec robustnost);
plain r64 staje dokazano. Proba + gate nakon toga (nepromijenjen
produkcijski prompt).

## 9B nastavak po nalogu: format-spec proba + r16eh-01 (2026-10-05)

Dva paralelna kraka: (1) format-spec proba (baza vs r6402, eksplicitna
XML gramatika u promptu — odgovara da li je problem u tezinama ili
protokolu); (2) r16eh-01 FRESH, SAMO embed_tokens/lm_head (bez
attentiona, ~16M param — sigurno staje).

## 9B probeeh: embed-only proba direktno kernelom (2026-10-05)

Download adaptera zapinje na sesijskom limitu — zaobilazak: proba cita
adapter iz kernel_sources (obrazac probe04/05), bez downloada.

## 9B PREKRETNICA: format-spec proba 3/5 (2026-10-05)

Baza (netrenirana!) + eksplicitna XML gramatika u promptu: 3/5 kanonskih;
r6402 + spec: 3/5. Tezine MOGU emitovati dijalekt — problem je PROTOKOL
(default prompt ga ne okida), ne tezine. Trening uzorci nemaju system
poruku, a produkcijski SYSTEM nema format-spec (2B/4B to ne treba jer
imaju nativni tool template).
ODLUKA: proizvodni prompt se NE dira (uporedivost gateova); robustnost
se uci kroz podatke.

## Mix v0.33 sa format-spec varijantama (2026-10-05)

v0.33 = v0.32 (1191) + 149 spec-varijanti (svaki 3. tool uzorak;
bosanski SPEC system) = 1340. Varijante samo u mixu.
Hub rev 616dca43.

## S43: 98 GOLD + mix v0.34 (2026-10-07)

S43 (multi-step/confirmation/paketi): 58 AG (0633-0692) + 40 FC
(1305-1344); 2 odbacena validatorom (rm -rf deny-obrazac).
FC 1329, AG 689; audit 0 kontradikcija; testovi 37/37.
Mix v0.34 = v0.33 + S43 + 26 S43-spec-varijanti = 1464
(688 FC + 280 BC + 496 AG). Leakage: 0 novih preklapanja.

## S43 v2: +60 + DPO balans + mix v0.35 (2026-10-07)

S43 v2: 20 AG (samba/nfs/mail/diagnostika) + 20 FC (paketi/fajlovi/portovi)
+ 20 BC (BiH geografija/kultura) = 60 GOLD; 7 zamjena duplikata.
DPO v0.3: 150 parova (140 + 10 balansiranih confirm/act).
FC 1349, AG 709, BC 1138; testovi 37/37; audit 0 kontradikcija.
Mix v0.35 = v0.34 + S43v2 + 10 spec-varijanti = 1534.
S43 ukupno: 158 uzoraka.

## S43 v3: +60 + DPO v0.4 + mix v0.36 (2026-10-08)

## S44: +70 + DPO v0.5 + mix v0.37 (2026-10-08)

S44: 20 AG (nut/samba/dns/backup) + 20 FC (paketi/fajlovi/portovi)
+ 20 BC (BiH istorija/pisci/priroda) + 10 DPO balansiranih.
FC 1389, AG 749, BC 1178; DPO v0.5: 170 parova.
Testovi 37/37; audit 0; leakage čist.
Mix v0.37 = v0.36 + S44 + 9 spec-varijanti = 1670.
S43+S44 ukupno: 288 uzoraka.

S43 v3: 20 AG (named/dns/mail/backup) + 20 FC (samba/paketi/fajlovi)
+ 20 BC (BiH gradovi/planine/pisci); 1 zamjena duplikata.
DPO v0.4: 160 parova (150 + 10 balansiranih).
FC 1369, AG 729, BC 1158; testovi 37/37; audit 0; leakage čist.
Mix v0.36 = v0.35 + S43v3 + 10 spec-varijanti = 1604.
S43 ukupno: 218 uzoraka.

## 9B gate05: spec radi, ali 9B gubi — TRAG PAUZIRAN (2026-10-07)

## 9B prioritet 2: v0.5 (r6405+dpo02) na Hubu, gate06 sa spec (2026-10-07)

## 9B r64-06 v1 fail: DataParallel (2026-10-09) — fix + re-run

r64-06 v1 pao: SFTTrainer ne podrzava nn.DataParallel (sesija dala
2 GPU-a, device_map auto shardovao). Fix: CUDA_VISIBLE_DEVICES=0
u preflight celiji + assert device_count==1 (obavezno za sve buduce
trening kernele). v2 pushan.
v2 pao: novi TRL chunked_logprob kernel trazi sm80+, T4 je sm75
(plutajuci pip upgrade slomio radni lanac!). Dijagnoza mikro-kernelima
(stat06/getver obrazac). Fix: pin transformers==5.19.0, trl==1.14.2,
peft==0.21.2, accelerate==1.15.0, datasets==5.1.0 (provjereno dobre
iz r6405 manifesta). v3 pushan. LEKCIJA: pinuj verzije u notebooku,
nikad plutajuci upgrade na trening kernelima.

## 9B gate06: DPO nula dobitka — 9B EKSPERIMENTALAN (2026-10-08)

## 4B joint-31 na Thunderu (2026-10-09): dpo01 + mix v0.37

4B lanac odmrzнут: nastavak v0.4-DPO adaptera sa S44 podacima (mix v0.37,
1670 uzoraka) na A100. Cilj v0.5-4B.

## 9B r64-06 na v0.35 sa r6405 (2026-10-08, bez Thundera)

## 9B Thunder r64e x3: embed hipoteza mrtva — PAUZA DEFINITIVNA (2026-10-09)

Thunder r64e-01/02/03 (r64+embed, A100): eval 0.86→0.81, probe 0/5-0/5-0/5.
Embed ne instalira gramatiku ni uz kapacitet. Bilans 9B: SFT 9 epoha
(r16x5, r64x4) + DPO x2 + embed x3 + rankovi + spec-protokol (0.633 max).
Svaka metoda isprobana; format dolazi samo iz prompta.
Thunder se preusmjerava: 4B joint-31 (dpo01 + mix v0.37).

## 9B gate07: BS-spec na v0.3 — protokol dominira (2026-10-09)

v0.3 Q8 + BS-spec, kompletnih 48: tool 0.60, args 0.346, high_level 1.0.
Gate vs 2B+spec: 4W-21T-23L. Zanimljivo: jedan output doslovno kopirao
placeholder <function=ime_alata> iz speca.
ZAKLJUCAK: protokol (EN 0.633 / BS 0.60) dominira nad treningom
(v0.3 vs v0.4 vs r6405 sve ~0.6); SFT/DPO/rank ne micu 9B sa mjesta.
9B ostaje eksperimentalno.

## 9B protokol-varijante: BS-spec 4/5 pobjeđuje (2026-10-09)

EN-spec 3/5, BS-spec 4/5, fewshot 2/5 (na r6406). BS ostaje bosanski.
ODLUKA: gate07 = postojeci v0.3 Q8 + BS-spec (jeftino, bez pipelinea);
tek onda merge r6406 ako BS pokaze strop.

## 9B proba r64-06: 0/5 — protokol-varijante test (2026-10-09)

v0.35 (2 epohe) ne prenosi format na default prompt.
ODLUKA: umjesto trece epohe naslijepo — test EN-spec vs BS-spec vs
few-shot direktno na r6406 (15 generacija, ~30 min, bez treninga).
Najbolji protokol ide u puni gate.

Thunder nedostupan → povratak na Kaggle T4: r64-06 (mix v0.35/1534
sa r6405 adaptera). DPO-02 baza za kasnije.

v0.5 (r6405+dpo02) + spec: tool 0.633 — identicno v0.4 (0W-48T-0L).
Gate vs 2B+spec: 3W-27T-18L. Nema releasea; kartica postavljena na
EKSPERIMENTALNO (posteno: fajlovi postoje, live nije).
Mikro-kernel trik (get06) zaobilazi stall pri downloadu velikih outputa.

Q8 427 tenzora → model-q8-v0.5.gguf. Upload se zavrsio prije aborta
(Hub no-op potvrda). Gate06 kernel u toku.

## 9B prioritet: r64-05 + dpo_9b_v0.2 (2026-10-07)

## 9B DPO-02 GOTOV (loss 0.66), merge mq05 u toku (2026-10-07)

Dvostepeni merge (r6405 + dpo02) → Q8 v0.5 → gate sa spec protokolom.

## 9B r64-05 GOTOV + DPO-02 pokrenut (2026-10-07)

Cilj: najbolja moguca 9B verzija (2B/4B/9B pokrivenost).
r64-05: treca epoha v0.33 sa r6404 adaptera.
dpo_9b_v0.2 (36 parova: 27 format + 9 spec-mined iz gate05 —
9B grijesi, 2B+spec tacan, isti prompt).

r6404 (v0.33 x2) + spec: tool 0.633 (19/30), args 0.423, kompletnih 48/48.
2B v0.5 + ISTI spec (lokalni re-gate): tool 0.90, args 0.808.
Gate 9B vs 2B pod spec protokolom: 3W-27T-18L — 9B odlucno slabiji.
Zanimljivo: spec pomaze 2B tool (0.80→0.90) ali rusi confirmation (0.8→0.4).
ZAKLJUCAK: spec otkljucao format ali ne i kvalitet; 9B ispod 2B uz iste
uslove. Nema 9B releasea. Pauza sa kompletnim dokazima (SFT/DPO/spec/rank).

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
