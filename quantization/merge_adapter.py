#!/usr/bin/env python3
"""Merge baze + LoRA adaptera u pune tezine (za GGUF konverziju).

Upotreba: python quantization/merge_adapter.py --base <hf-dir-ili-repo> \
  --adapter <adapter-dir> --out <merged-dir> [--dtype bf16]

Radi na CPU (potrebno ~8 GB RAM-a za 2B bf16). Izlaz: kompletan HF dir
spreman za convert_hf_to_gguf.py.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float32"])
    ap.add_argument("--rm-base-after-load", action="store_true",
                    help="obrisi --base dir nakon ucitavanja u RAM (stednja diska; samo za jednokratne dir-ove, NIKAD za HF cache)")
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    dtype = torch.bfloat16 if a.dtype == "bfloat16" else torch.float32
    print(f"[merge] baza: {a.base} | adapter: {a.adapter} | dtype: {a.dtype}", flush=True)
    base = AutoModelForCausalLM.from_pretrained(
        a.base, dtype=dtype, device_map="cpu", trust_remote_code=True)
    tok = AutoTokenizer.from_pretrained(a.base, trust_remote_code=False)
    if a.rm_base_after_load:
        import shutil as _sh
        assert Path(a.base).is_dir() and "huggingface" not in str(Path(a.base).resolve()), \
            "rm-base-after-load dozvoljen samo za jednokratne dir-ove"
        _sh.rmtree(a.base)
        print(f"[merge] baza obrisana sa diska (težine u RAM-u)", flush=True)
    model = PeftModel.from_pretrained(base, a.adapter)
    merged = model.merge_and_unload()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(out)
    tok.save_pretrained(out)
    print(f"[merge] gotovo: {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
