# Vast GPU worker — stateless specifikacija (v0.1, SUPERSEDED)

> Status 2026-09-18: Vast nikad nije aktiviran — **Kaggle Free GPU je izabran
> kao worker** (vidi `workers/kaggle/`, 12+ uspješnih jobova). Ovaj direktorij
> ostaje kao alternativni dizajn; ne brisati dok se ne potvrdi da Kaggle
> pokriva sve potrebe.
#
# Princip: Vast instanca je zamjenjiva. Source of truth su Oracle i/ili
# Hugging Face Hub. Gubitak instance ne smije značiti gubitak projekta.

worker:
  image: "pytorch/pytorch:2.4.0-cuda12.1-cudnn9-devel  # primjer; pinovati pri prvom runu"
  gpu_target: "RTX 4090 24GB (ili ekvivalent); min 16GB VRAM za LoRA 2B"
  inputs_from_oracle:
    - training config (configs/training/*.yaml)
    - dataset snapshot (HF dataset repo + revision)
    - base model (HF repo + revision)
    - experiment manifest (experiment_id, seed, git commit)
  outputs_to_hf_oracle:
    - LoRA adapteri + checkpointi
    - training metrike (loss, grad norm, GPU mem)
    - experiment manifest sa checksumama
  must_not:
    - čuvati jedinu kopiju bilo čega na workeru
    - commitovati tajne; HF token isključivo iz env/secret storagea

startup_script: workers/vast/startup.sh   # TODO: napisati prije prvog GPU runa
sync_script: workers/vast/sync.sh         # TODO: push artefakata na HF + manifest na Oracle
