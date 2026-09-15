# Model Card TEMPLATE — popuniti prije SVAKOG publisha (gate iz docs/HF_PUBLISHING.md)

# <model-id>

**Base model:** <npr. alphaedge-ai/Qwen3.5-2B-bos-32768 @ rev `...`>
**Metoda:** <LoRA SFT, r=.., alpha=.., target modules>
**Jezik:** bosanski (ijekavica)
**Kontekst:** <npr. 32768 deployment>
**Thinking/non-thinking:** zajedničke težine; `enable_thinking` zastavica chat templatea

## Dataseti

- <agentmujo-function-calling @ verzija, HF link, broj uzoraka>
- <agentmujo-agentic-terminal @ verzija, HF link, broj uzoraka>

## Benchmark (AgentMujo-Bench, 16 kategorija)

| Kategorija | Base | Fine-tuned | Q8 |
|---|---|---|---|
| tool_selection | | | |
| argument_accuracy | | | |
| ... | | | |

## Kvantizacija

<metoda: GGUF Q8_0 / ..., delta tabela vs full>

## Ograničenja

- <poznata ograničenja, sigurnosne napomene, Policy Engine je obavezan>

## Licenca

<Apache-2.0 + uslovi Qwen porodice; link na bazni model card>
