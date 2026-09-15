---
language:
  - bs
license: apache-2.0
task_categories:
  - question-answering
tags:
  - function-calling
  - bosnian
  - ai-agents
  - agentmujo
---

# agentmujo-function-calling (v0.1.0 — MVP)

Ručno dizajniran kanonski skup za **function calling na bosanskom jeziku
(ijekavica)**, dio [AgentMujo Training Frameworka](https://github.com/xnet-ba/agentmujo-training)
(`configs/tools.yaml` je Single Source of Truth za alate).

- **Verzija:** 0.1.0 · **Uzoraka:** 127 · **Jezik:** bs-ijekavica
- **Format:** JSONL; svaki red: `id, version, language, task, difficulty,
  enable_thinking, messages[] (user/assistant/tool + tool_calls[]), metadata{}`
  (schema: `schemas/dataset.schema.json` u framework repou).
- **Alati:** service_status, service_restart, service_logs, disk_usage,
  memory_usage, cpu_usage, process_list, network_status, port_check, terminal.
- **Posebno:** sadrži no-tool uzorke (opća pitanja bez poziva alata) i
  odbijanja opasnih zahtjeva (curl|bash, /etc/shadow, iptables -F).
- **Kvalitet:** svi uzorci prolaze validator (GOLD/SILVER/BRONZE/REJECT);
  trenutno 127/127 ACCEPT. Cilj faze 1: 100–300 uzoraka (u ciljanom opsegu 100-300).
- **Leakage kontrola:** train/valid/test split 80/10/10 je hash-deterministički
  i disjunktan; benchmark (`AgentMujo-Bench`) je potpuno odvojen skup.
- **Metodologija:** ručno, human-reviewed. Bez ličnih podataka, bez tajni.
- **Licenca:** Apache-2.0.

Status: MVP za validaciju pipelinea (format, tokenizer, chat template,
evaluator). Proširenje slijedi nakon potvrde trening petlje.
