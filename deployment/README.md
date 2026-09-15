# Deployment profili (Ollama)

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
