# AgentMujo Training Framework — PROJECT SPEC (v0.1)

Datum: 2026-09-15 · Status: framework skeleton, BEZ treninga · Verzija: 0.1.0

## 1. Cilj

Razviti reproducibilan sistem za fine-tuning malih jezičkih modela
(0.5B–4B) za bosanski jezik (ijekavica), sa prioritetima:

1. bosanski jezik i ijekavica (naslijeđeno od baze, ne trenirati od nule),
2. function calling (intent → tool → argumenti → validan poziv),
3. agentic/terminal ponašanje (dijagnoza → akcija → opservacija → verifikacija),
4. pouzdano višekoračno izvršavanje zadataka,
5. verifikacija rezultata (nikada ne pretpostaviti uspjeh akcije),
6. sigurnost pri izvršavanju komandi (Policy Engine, ne fine-tuning),
7. brza, memorijski efikasna kvantizirana (Q8) deployment verzija.

Cilj NIJE još jedan chatbot, već jezgra AgentMujo AI agenta koja radi
lokalno i brzo.

## 2. Arhitektura

```
USER REQUEST
  → MODEL (bosanski + reasoning + tool call)
  → TOOL CALL (canonical registry, JSON Schema)
  → POLICY ENGINE (allow / confirmation_required / deny)
  → EXECUTOR → LINUX
  → RESULT (skraćen/filtriran kroz Context Manager)
  → MODEL (sljedeća akcija ili finalni odgovor, uz VERIFY korak)
```

Ključne odluke v0.1 (potvrđene provjerom modela, ne pretpostavke):

- **D1 — Thinking/non-thinking je jedan model.** Chat template baznog
  modela podržava `enable_thinking` zastavicu: `true` otvara `<think>`
  reasoning, odsustvo daje prazan `<think>\n\n</think>` (non-thinking).
  Trening je ZAJEDNIČKI (uzorci sa `enable_thinking: true/false`);
  deployment profili se razlikuju samo po zastavici + samplingu.
  Četiri varijante (thinking / non-thinking / Q8 × 2) dijele iste težine.
- **D2 — Tool calling je nativan.** Format
  `<tool_call><function=N><parameter=P>v</parameter></function></tool_call>`
  i `<tool_response>` su dio tokenizera i chat templatea — dataseti ga
  moraju slijediti doslovno.
- **D3 — Terminal je fallback.** High-level alat (npr. `service_restart`)
  uvijek ima prednost nad `terminal("systemctl ...")`. Terminal prolazi
  kroz Policy Engine; fine-tuning nikada nije sigurnosni mehanizam.
- **D4 — Framework je model-agnostičan.** `configs/models.yaml` je
  registar; novi model 0.5B–4B dodaje se kao unos, bez redizajna.
- **D5 — Dataseti su odvojeni od koda.** GitHub: kod/scheme/config/testovi.
  Hugging Face Hub: dataseti, modeli, adapteri, benchmark artefakti.
- **D6 — Vast je stateless.** Source of truth su Oracle i/ili HF Hub;
  gubitak Vast instance ne gubi projekat (`workers/vast/`).

## 3. Model lineage

```
alphaedge-ai/Qwen3.5-2B-bos-32768 (baza, pin: 2f89b8332c..., 2026-05-20)
  → Function Calling SFT (LoRA, configs/training/sft_function_calling.yaml)
  → Agentic/Terminal SFT (LoRA nastavak, sft_agentic.yaml)
  → Evaluation / AgentMujo-Bench
  → najbolji checkpoint/adapter → merge po potrebi
  → Q8 kvantizacija (GGUF Q8_0, validirano: Ollama već servira Q8_0 sa tools+thinking)
  → AgentMujo deployment model (4 profila iz D1)
```

Provjereni metapodaci baze (2026-09-15, `hf models info` + README + config):

- arhitektura `Qwen3_5ForConditionalGeneration`, 1.77B params (trimmed sa 2.21B),
- vokabular 32768 (trimmed sa 248320, fineweb-2, 200k tekstova),
- nativni kontekst 262144, deployment cilj 32768; `tie_word_embeddings: true`,
- dtype BF16, safetensors; licenca **Apache-2.0**; jezik `bos`;
- tokenizer `Qwen2Tokenizer` + posebni tokeni za alate i `<think>`;
- učitavanje: `AutoModelForCausalLM` za tekst (HF meta spominje i
  `AutoModelForMultimodalLM` — tekstualni put je kanonski za trening);
- instalirani `transformers 5.16.1` podržava `qwen3_5`; TRL/PEFT/datasets
  zasad NISU na Oracleu (namjerno — trening ide na Vast GPU).

## 4. Dataseti

| Skup | Status v0.1 | Cilj faze 1 |
|---|---|---|
| agentmujo-function-calling | MVP 12 uzoraka (`datasets/canonical/function_calling_v0.1.jsonl`) | 100–300 |
| agentmujo-agentic-terminal | MVP 5 tragova (`agentic_terminal_v0.1.jsonl`) | 100–300 |
| tool-selection, argument-generation, verification, safety | planirani (izdvojeni iz prva dva) | nakon pipeline validacije |
| bosnian-core | ODGOĐENO dok benchmark ne pokaže potrebu | — |
| linux-diagnostics, business | planirani | faza 2+ |

Svaki uzorak: stabilan ID (`amj-*`), verzija, jezik, zadatak, težina,
`messages[]` (user/assistant/tool + `tool_calls[]`), metadata
(izvor, GOLD/SILVER/BRONZE, verification status). Train/valid/test su
disjunktni (`amj dataset split`, hash po ID-u). Benchmark je potpuno
odvojen od trening skupova.

## 5. Trening strategija

- Metoda: LoRA SFT (`r=16, alpha=32, dropout=0.05` kao polazna tačka);
  puna fine-tuning Якo tek ako benchmark pokaže da LoRA ne zatvara gap.
- Faza 1 (function calling): `lr=2e-4, ep=3, max_seq=8192`.
- Faza 2 (agentic, nastavak): `lr=1e-4, ep=3, max_seq=16384`.
- Stack: Transformers + Datasets + TRL + PEFT + Accelerate + PyTorch
  (+ bitsandbytes na Vast GPU ako je podržan).
- **Gate: NIJEDAN GPU run dok validatori + benchmark + TEST_PLAN gate
  ne budu zeleni** (vidi `docs/TEST_PLAN.md`). CLI `train` je namjerno
  stub u v0.1.

## 6. Evaluacija (AgentMujo-Bench)

10 kategorija (`benchmark/cases_v0.1.jsonl`, 8 starter slučajeva):
bosnian_quality, tool_selection, argument_accuracy, tool_call_validity,
json_validity, multi_step, terminal_accuracy, verification, safety,
task_success. Poređenja: base × fine-tuned × thinking × non-thinking ×
full × Q8. Metrike: tool_selection_accuracy, argument_accuracy,
valid_tool_call_rate, json_validity, multi_step_success,
terminal_accuracy, verification_success, safety_accuracy,
task_completion_rate, bosnian_quality, latency, tokens_generated, GPU mem.
v0.1 scorer je deterministički rule-based (bez LLM-sudije).

## 7. Vast / Oracle workflow

- Oracle (ARM64, 24GB RAM): control plane — kod, config, validatori,
  benchmark, registri, manifesti; NIKADA teški trening.
- Vast (GPU worker, stateless): povuče pinovani config + dataset snapshot
  + bazni model → trenira → vrati adaptere, metrike i manifest na HF/Oracle.
- HF autentikacija: `hf auth login`, token u credential storageu, nikada u gitu.

## 8. GitHub / Hugging Face workflow

- GitHub (`xnet-ba/agentmujo-training`, predloženo — repo još ne postoji,
  struktura je lokalno pripremljena): kod, scheme, config, testovi, docs.
- HF Hub: dataseti (`agentmujo-*`), modeli/adapteri, benchmark artefakti,
  svaki sa karticom (model card: baza, revizija, dataseti, metodologija,
  benchmark, kvantizacija, licence, limitations).
- Publish gate: manifest + validator ACCEPT + benchmark + provjera licence
  + bez tajni (detalji: `docs/HF_PUBLISHING.md`).

## 9. Kvantizacija

Pipeline: eval → merge po potrebi → Q8 (GGUF Q8_0 primarno, Ollama profil
već dokazan u produkciji: `qwen3.5-2b-bos-q8`, 1.5GB, tools+thinking,
kontekst 262144) → re-eval → release. Q8 se benchmarkira protiv
nekvantiziranog modela (kvalitet, function-calling tačnost, latencija,
RAM, veličina). Bez pretpostavke o 100% očuvanju kvaliteta.

## 10. Release strategija

Četiri profila iz zajedničke osnove (D1): thinking, non-thinking,
Q8-thinking, Q8-non-thinking. Release sadrži: težine/adaptere, model card,
benchmark izvještaj (svih 10 kategorija × 4 profila), kvantizacioni
izvještaj, reproducibility manifest (experiment ID, revizije, seed,
hardware, checksumi).
