# TEST PLAN — gateovi (status: SVI ZELENI, održava se)

## TP-0: Statički gate — ZELEN

- [x] `pytest -q` → 31/31 zeleno (registry, validator, benchmark, safety, policy, agent, leakage)
- [x] `amj tools validate` → 10 alata, politike ispravne
- [x] `amj dataset validate` → svi skupovi ACCEPT, 0 REJECT
- [x] `amj benchmark run --cases benchmark/cases_v0.4.jsonl` → 40 slučajeva

## TP-1: Dataset scale-up gate — ZELEN

1. [x] function-calling 192, agentic-terminal 141, bosnian-core 120 (+pogledi).
2. [x] split freeze + `leakage_report.json` + CI test protiv kontaminacije.
3. [x] Safety paket: 31+ odbijanja/potvrda.

## TP-2: Bazni benchmark — ZELEN

[v] AgentMujo-Bench v0.4 (40 slučajeva) protiv baze; bosnian-core bio odgođen
pa reaktiviran nakon dokazanog forgettinga (vidi `docs/BOSNIAN_PROBE.md`).

## TP-3: Smoke/dev trening — ZELEN

[v] LoRA SFT na Kaggle T4 kroz job pipeline; eval svakog adaptera prije releasea.

## TP-4: Kvantizacioni gate — ZELEN (Q8 v0.4 live)

[v] Full vs Q8 delta tabela u `docs/QUANT_EVAL.md`; release samo uz izvještaj.

## Abort kriteriji

Prekinuti i vratiti se na dataset/dizajn ako: `safety_accuracy < 1.0` na
deny slučajevima, `json_validity` padne ispod 0.95, ili Q8 izgubi >5pp
`task_completion_rate` bez jasnog uzroka.
