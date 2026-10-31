---
language:
  - bs
license: other
task_categories:
  - text-generation
pretty_name: AgentMujo Dataset v0.3.0
---

# AgentMujo Dataset Card — v0.3.0

**Ukupno redova:** 3996
**Kategorije:** agentic-evaluation, agentic-tasks, bosnian-language, coding, function-calling, instructions, knowledge, linux-terminal, preference-dpo, rag-memory, reasoning, safety, tool-use-mcp
**Gapovi:** -

| Dataset | Kategorije | Redovi | SHA256 |
|---|---|---:|---|
| agentmujo-bosnian-language | bosnian-language, instructions | 1178 | `596143811151b11b` |
| agentmujo-safety | safety | 60 | `91f98210d4583a9e` |
| agentmujo-reasoning | reasoning | 75 | `9d8deb8bb11ddd47` |
| agentmujo-function-calling | function-calling, tool-use-mcp | 1374 | `034da077ef1bc141` |
| agentmujo-agentic-tasks | agentic-tasks, linux-terminal | 739 | `32c98769754dafdf` |
| agentmujo-bosnian-knowledge | knowledge | 200 | `ef1b322940f5f650` |
| agentmujo-coding | coding | 100 | `2e1558803ec4b442` |
| agentmujo-rag-memory | rag-memory | 100 | `1b7e7234d64f2350` |
| agentmujo-preference-dpo | preference-dpo | 170 | `394fbce9d0d22c32` |

## Benchmark (evaluation, held-out)
| Benchmark | Kategorija | Zadaci | SHA256 |
|---|---|---:|---|
| agentmujo-agentic-evaluation | agentic-evaluation | 50 | `71cb55367a79e723` |

## Licence
- knowledge/RAG: CC BY-SA 4.0 (Wikipedia; attribution URL u metadata).
- coding: Apache-2.0 (vlastiti repo kod).
- benchmark: Apache-2.0 (held-out, nije trening).
- preference/ostalo: interno/Apache-2.0 po evidenciji.

## Napomene
- Bez LUMI GPU za obradu podataka.
- Gapovi nisu popunjeni nekvalitetnim podacima.
