# Dataset Card TEMPLATE — popuniti prije SVAKOG publisha

# <dataset-id>

**Verzija:** <0.x.y> · **Jezik:** bs-ijekavica · **Splitovi:** train/valid/test 80/10/10
**Veličina:** <N uzoraka> · **Kvalitet:** GOLD/SILVER/BRONZE raspodjela

## Format

Svaki red je JSON sa: `id, version, language, task, difficulty,
enable_thinking, messages[] (user/assistant/tool + tool_calls[]), metadata{}`
(vidi `schemas/dataset.schema.json`; registry: `configs/tools.yaml`).

## Metodologija

<ručno / generator + verzija generatora / human-reviewed udio>

## Leakage kontrola

<hash dedup izvještaj; potvrda disjunktnosti train/valid/test i benchmarka>

## Licenca i privatnost

<licenca; potvrda da nema tajni/privatnih podataka>
