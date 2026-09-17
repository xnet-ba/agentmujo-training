---
language:
  - bs
license: apache-2.0
task_categories:
  - question-answering
tags:
  - ai-agents
  - joint-training
  - replay
  - bosnian
  - agentmujo
---

# agentmujo-joint-01 (v0.1.0)

Joint trening mix protiv forgettinga: **samo train splitovi** (test/valid
ostaju čisti za evaluaciju).

- **Sastav (295):** 117 function-calling + 88 agentic-terminal + 90 bosnian-core.
- **Metoda:** deterministički shuffle (seed 11); ID-evi jedinstveni.
- **Format:** JSONL, kanonska schema. Validacija: 295/295 ACCEPT.
- **Licenca:** Apache-2.0. Bez ličnih podataka, bez tajni.
