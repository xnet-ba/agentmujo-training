---
language:
  - bs
license: apache-2.0
task_categories:
  - question-answering
tags:
  - bosnian
  - general-language
  - agentmujo
---

# agentmujo-bosnian-core (v0.1.0 — serija 1)

Opći bosanski jezik (ijekavica) **bez alata** — replay protiv catastrophic
forgettinga izazvanog uskim tool SFT-om (dokazano re-probom, vidi
`docs/BOSNIAN_PROBE.md`).

- **Verzija:** 0.1.0 · **Uzoraka:** 30 · **Jezik:** bs-ijekavica
- **Sadržaj:** razgovor, tačno opće znanje, gramatika (padeži, da li/je li),
  prijevodi EN↔BS, sažeci. Svi odgovori provjereno tačni — ispravljaju
  točno one halucinacije koje je baza pokazala (džep, akuzativ, mlijeko).
- **Format:** JSONL, ista schema (`task: bosnian-core`, bez `tool_calls`).
- **Kvalitet:** 30/30 ACCEPT, human-reviewed.
- **Licenca:** Apache-2.0. Bez ličnih podataka, bez tajni.
