---
language:
  - bs
license: apache-2.0
task_categories:
  - question-answering
tags:
  - ai-agents
  - terminal
  - bosnian
  - agentmujo
---

# agentmujo-agentic-terminal (v0.1.0 — MVP)

Ručno dizajnirani **višekoračni agentic/terminal tragovi** na bosanskom
(ijekavica), dio [AgentMujo Training Frameworka](https://github.com/xnet-ba/agentmujo-training):
problem → dijagnoza → tool call → opservacija → analiza →
akcija → **verifikacija** → finalni odgovor. Agent nikada ne pretpostavlja
da je akcija uspjela.

- **Verzija:** 0.1.0 · **Tragova:** 50 · **Jezik:** bs-ijekavica
- **Format:** JSONL, ista schema kao function-calling
  (`schemas/dataset.schema.json` u framework repou).
- **Obrasci:** nginx port-konflikt (apache2), redis failed→restart→active
  sa verifikacijom, docker/disk lanac, RAM istraga, odbijanja destruktivnih
  zahtjeva (rm -rf, pipe-to-shell kao root, iptables flush).
- **Kvalitet:** svi uzorci prolaze validator (trenutno 50/50 ACCEPT).
  Cilj faze 1: 100–300 tragova.
- **Leakage kontrola:** disjunktno od train/valid/test splitova i benchmarka.
- **Metodologija:** ručno, human-reviewed. Bez ličnih podataka, bez tajni.
- **Licenca:** Apache-2.0.

Status: MVP za validaciju multi-step treninga. Terminal je low-level
fallback — high-level alati imaju prednost; sigurnost osigurava Policy
Engine u runtimeu, ne ovaj dataset.
