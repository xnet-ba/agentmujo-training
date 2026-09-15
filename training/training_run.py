#!/usr/bin/env python3
"""Faza 1/2 LoRA SFT run — izvršava se na Vast GPU workeru (ne na Oracleu).

Ulaz: training config (configs/training/*.yaml) + experiment manifest.
Izlaz: LoRA adapteri, checkpointi, training metrike, popunjen manifest.

Zahtijeva train extras: pip install -e ".[train]"
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def build_experiment_manifest(args, cfg: dict) -> dict:
    git_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    return {
        "experiment_id": cfg.get("experiment_id"),
        "base_model": cfg.get("base_model"),
        "base_revision": cfg.get("base_revision"),
        "dataset": cfg.get("dataset"),
        "training_config": args.config,
        "git_commit": git_commit,
        "seed": cfg.get("seed", 42),
        "hardware": args.hardware or "vast-gpu-tbd",
        "metrics_train": {},
        "metrics_eval": {},
        "artifacts": [],
        "checksums": {},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="AgentMujo LoRA SFT (Vast worker)")
    ap.add_argument("--config", required=True, help="configs/training/*.yaml")
    ap.add_argument("--out", required=True, help="direktorij za adaptere + manifest")
    ap.add_argument("--hardware", default=None)
    ap.add_argument("--dry-run", action="store_true", help="samo manifest, bez GPU-a")
    a = ap.parse_args()

    try:
        import yaml  # noqa
    except ImportError:
        print("Nedostaje pyyaml: pip install -e .")
        return 2
    cfg = yaml.safe_load(Path(a.config).read_text(encoding="utf-8"))
    manifest = build_experiment_manifest(a, cfg)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "experiment_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Manifest: {out / 'experiment_manifest.json'}")

    if a.dry_run:
        print("DRY-RUN: trening preskočen (validacija configa + manifesta OK).")
        print(f"  base={cfg.get('base_model')}@{str(cfg.get('base_revision'))[:12]}")
        print(f"  dataset={cfg.get('dataset')} seed={cfg.get('seed')}")
        return 0

    # Stvarni trening — TRL SFTTrainer + PEFT LoRA (samo na GPU workeru).
    try:
        import torch  # noqa
        from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa
        from datasets import load_dataset  # noqa
        from peft import LoraConfig  # noqa
        from trl import SFTTrainer, SFTConfig  # noqa
    except ImportError as e:
        print(f"Nedostaju train zavisnosti ({e}): pip install -e .[train]")
        return 2

    print("TODO-faza: puni SFTTrainer run dolazi sa prvim GPU eksperimentom; "
          "config i manifest su spremni.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
