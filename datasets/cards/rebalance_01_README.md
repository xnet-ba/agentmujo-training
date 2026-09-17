---
language:
  - bs
license: apache-2.0
task_categories:
  - question-answering
tags:
  - ai-agents
  - function-calling
  - safety
  - bosnian
  - agentmujo
---

# agentmujo-rebalance-01 (v0.1.0)

Ciljani rebalansni mix za ispravku regresija nakon faze 2 (argument accuracy,
refusal, safety): deterministički sastavljen (seed 7) od postojećih uzoraka.

- **Sastav (100):** 31 safety/odbijanje + 35 function-calling + 34 agentic-terminal.
- **Format:** JSONL, ista schema (`schemas/dataset.schema.json` u
  [framework repou](https://github.com/xnet-ba/agentmujo-training)).
- **Kvalitet:** 100/100 ACCEPT kroz validator. Bez novih neprovjerenih uzoraka.
- **Licenca:** Apache-2.0. Bez ličnih podataka, bez tajni.
