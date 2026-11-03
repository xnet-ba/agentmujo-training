# Axolotl u AgentMujo projektu

**Odluka: DA** — Axolotl (Apache-2.0, 12.7k zvijezda) postaje trening backend
umjesto ručnih TRL skripti. Razlozi: jedan YAML za SFT+DPO, sample packing,
FSDP2/DeepSpeed za multi-GPU (LUMI, 4B/9B), `axolotl export` u GGUF
(zamjenjuje ručni convert+patch), Qwen3 podrška potvrđena.

## Kako radi (minimalna integracija)

Naš kanon drži tool_calls strukturno; `training/format.py::sample_to_text`
je jedini most do trening teksta. Axolotl dobija **već renderovan tekst**
(`type: completion`), pa je trening signal identičan starom TRL putu —
nema template migracije.

```bash
# 1. Export (lokalno ili u notebooku)
python scripts/export_axolotl.py --sft \
  --input datasets/splits/joint_train_v0.42.jsonl --output /tmp/axo_sft.jsonl
python scripts/export_axolotl.py --dpo \
  --inputs datasets/canonical/dpo_v0.6.jsonl datasets/canonical/dpo_v0.7.jsonl \
           datasets/canonical/dpo_v0.8.jsonl datasets/canonical/dpo_v0.9.jsonl \
  --output /tmp/axo_dpo.jsonl

# 2. Trening (treba GPU; Kaggle T4 ili LUMI)
export AXOLOTL_DO_NOT_TRACK=1   # telemetry off
axolotl train training/axolotl/qwen35-2b-sft.yml
axolotl train training/axolotl/qwen35-2b-dpo.yml  # uz lora_model_dir na SFT adapter
```

## Šta NIJE migrirano (namjerno)

- Kaggle TRL worker ostaje dok se Axolotl ne dokaže smoke runom na T4
  (axolotl install je težak: torch 2.14 + deepspeed).
- GGUF Q8 pipeline ostaje dok `axolotl export` ne prođe joint gate.
- DPO trenira SAMO na licencno čistim dpo kanonima (v0.6+: vlastiti +
  SWE-Gym MIT; OPUS/SWE-bench odbijeni).

## Napomene

- `sequence_len: 8192` (deploy cilj 32768; 8192 staje na T4 s packingom).
- bf16-LoRA po DATASET_TARGETS (4-bit zabranjen za Qwen3.5).
- LUMI: LAIF AI kontejneri već imaju torch/CUDA; axolotl ide u kontejner,
  ne na login node.
