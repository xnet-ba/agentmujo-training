# Deployment profili (Ollama)

## Živi modeli (2026-09-27)

| Alias (stabilan) | Verzija | Hub fajl | Napomena |
|---|---|---|---|
| `agentmujo-q8` | 2B v0.5 (joint-23) | model Q8 2B repo | default, 1.5GB |
| `agentmujo-4b-q8` | 4B v0.4-DPO | `model-q8-4b-dpo01.gguf` | veci, 3.9GB (`ollama cp` alias, shared blobs) |
| `agentmujo-q8-think` | 2B v0.4-think | — | think profil ostaje 2B v0.4 |

Pravilo: stabilni alias uvijek pokazuje na aktuelnu verziju;
verzionirani modeli (`agentmujo-4b-dpo01-q8`, `agentmujo-4b06-q8`) ostaju kao backup.

Thinking i non-thinking **dijele isti GGUF** — režim se bira runtime
zastavicom (`"think": true/false` u `/api/chat`), ne odvojenim fajlovima.
Ovo je direktna posljedica odluke D1 (zajedničke težine).

## Profili (4)

| Profil | GGUF | think flag | Modelfile |
|---|---|---|---|
| thinking | model.gguf (full ili Q8) | `true` | `deployment/Modelfile.thinking` |
| non-thinking | isti fajl | `false` | `deployment/Modelfile.nonthinking` |
| q8-thinking | model-q8.gguf | `true` | isti uz drugi FROM |
| q8-non-thinking | model-q8.gguf | `false` | isti uz drugi FROM |

## Build

```bash
ollama create agentmujo-thinking -f deployment/Modelfile.thinking
ollama create agentmujo-nonthinking -f deployment/Modelfile.nonthinking
# FROM liniju zamijeniti putem do konkretnog .gguf fajla prije builda.
```

Referentne vrijednosti preuzete iz produkcijskog `qwen3.5-2b-bos-q8`:
`num_ctx 16384`, capabilities tools+thinking, osnovni template iz GGUF
metapodataka (`TEMPLATE {{ .Prompt }}`).
