---
language:
  - bs
license: apache-2.0
task_categories:
  - question-answering
tags:
  - ai-agents
  - confirmation
  - safety
  - bosnian
  - agentmujo
---

# agentmujo-confirmation (v0.1.0)

Višeturni **confirmation obrasci**: model pita (uz posljedice) prije rizične
akcije i djeluje tek nakon eksplicitne potvrde. Sigurnosna politika je iznad
korisničke naredbe (uključuje uzorak gdje korisnik zabranjuje pitanja).

- **Uzoraka:** 20 (10 function-calling + 10 agentic-terminal)
- **Format:** JSONL, kanonska schema, `<think>` procjene rizika.
- **Kvalitet:** 20/20 ACCEPT, human-reviewed.
- **Licenca:** Apache-2.0. Bez ličnih podataka, bez tajni.
