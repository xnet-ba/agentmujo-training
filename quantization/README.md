# Kvantizacija — Q8 pipeline (GGUF Q8_0 primarno)

Referentni dokaz: `qwen3.5-2b-bos-q8` (GGUF Q8_0, 1.5 GB, kontekst 262144,
capabilities tools+thinking, deployment `num_ctx 16384`) već radi u
produkciji na ovom serveru. Pipeline ispod reproducira isti postupak za
buduće fine-tunirane težine.

## Protokol

```
FULL (safetensors, pinovana revizija)
  → convert_hf_to_gguf.py (llama.cpp, pinovana revizija)
  → model-f16.gguf (kontrolna tačka)
  → llama-quantize Q8_0
  → model-q8.gguf + SHA256 manifest
  → eval: bench full vs Q8 (docs/QUANT_EVAL.md)
  → release (samo uz kompletan delta izvještaj)
```

## Korištenje

```bash
bash quantization/convert_q8.sh <hf-repo> <revizija> <out-dir>
# npr: bash quantization/convert_q8.sh alphaedge-ai/Qwen3.5-2B-bos-32768 \
#        2f89b8332c352d01adebd88bba5d8a2f7adf8bd6 outputs/q8-base
```

Zahtijeva: `hf` CLI, Python 3.10+, C/C++ toolchain + cmake za llama.cpp
build (jednokratno). Konverzija 2B modela je CPU-izvodljiva (nekoliko
minuta); puni trening i dalje ide na Vast GPU.

## Kritične napomene (verificirano 2026-09-17)

- Konverzija MORA sa `--no-mtp`: checkpoint nema MTP tenzore; bez zastavice
  konverter upiše `block_count=25` + `nextn_predict_layers` i Ollama odbija
  fajl (`blk.24.attn_norm.weight not found`). Ispravno: 24 bloka, 320 tenzora.
- Trimmed vokabular treba tokenizer patch
  (`docs/patches/llama-tokenizer-qwen35-bos.patch`) — inače konverter ne
  prepoznaje pretokenizer.
- `quantization/patch_gguf.py` postoji kao zadnja linija odbrane za
  metapodatke (korišten dijagnostički; primarni put je ispravna konverzija).

- Nikada ne kvantizirati neevaluirani checkpoint (eval → merge → quant → re-eval).
- Svaki GGUF dobija SHA256 manifest pored fajla.
- Q8 bez delta tabele iz `docs/QUANT_EVAL.md` ne ide u release.
- `.gguf` fajlovi se NIKADA ne commitaju u git (vidi `.gitignore`).
