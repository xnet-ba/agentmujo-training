# TEST PLAN — prvi eksperiment (gate prije BILO KAKVOG treninga)

## TP-0: Statički gate (mora biti zelen — JESTE u v0.1)

- [x] `pytest -q` → 9/9 zeleno (registry, validator, benchmark, safety)
- [x] `amj tools validate` → 10 alata, politike ispravne
- [x] `amj dataset validate` → oba MVP skupa ACCEPT, 0 REJECT
- [x] `amj benchmark run --cases benchmark/cases_v0.1.jsonl` → 8 slučajeva se učitava

## TP-1: Dataset scale-up gate (prije GPU-a)

1. Proširiti function-calling na 100–300 uzoraka, agentic-terminal na
   100–300 — istim formatom; svaki prolazi validator (GOLD/SILVER cilj).
2. `amj dataset split` → train/valid/test 80/10/10; provjeriti 0 preklopa
   ID-eva i hash-eva sadržaja između splitova i benchmarka.
3. Safety paket: min 30 odbijenih/zatraženih-potvrda slučajeva
   (rm -rf, mkfs, dd, iptables -F, pipe-to-shell, exfiltracija tajni).

## TP-2: Bazni benchmark (prije treninga)

Pokrenuti AgentMujo-Bench protiv BAZE u sva 4 profila
(thinking/non-thinking × full/Q8) i zabilježiti svih 16 kategorija (v0.2).
Ovo je nulta tačka — bez nje se napredak ne može mjeriti.
Bosanski kvalitet posebno: ako baza zadovoljava, `bosnian-core` ostaje odgođen.

## TP-3: Smoke trening (prvi GPU run, minimalan)

- LoRA `r=8`, 1 epoha, 10% podataka, `max_seq=4096`, jedan seed.
- Uspjeh = loss pada, `valid_tool_call_rate` ne pada ispod baze,
  adapter se učitava i generiše validan `<tool_call>` format.
- Tek onda puni run faze 1 (config u `configs/training/`), pa faza 2.

## TP-4: Kvantizacioni gate

Q8 (GGUF Q8_0) → ponoviti cijeli bench → objaviti delta tabelu
(kvalitet, argument accuracy, latencija, RAM, veličina). Release samo uz
kompletan izvještaj.

## Abort kriteriji

Prekinuti i vratiti se na dataset/dizajn ako: `safety_accuracy < 1.0` na
deny slučajevima, `json_validity` padne ispod 0.95, ili Q8 izgubi >5pp
`task_completion_rate` bez jasnog uzroka.
