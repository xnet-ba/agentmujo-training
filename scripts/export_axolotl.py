#!/usr/bin/env python3
"""Kanon/joint -> Axolotl-ready JSONL (isti trening signal kao training/format.py).

SFT: redovi postaju {"text": sample_to_text(row)} (ChatML tokeni vec ugradeni,
axolotl type completion, BEZ dodatnog chat templatea).
DPO: ravna prompt/chosen/rejected polja iz dpo kanona idu direktno (vec tekst).

Koristenje:
  python scripts/export_axolotl.py --sft --input datasets/splits/joint_train_v0.42.jsonl --output /tmp/axo_sft.jsonl
  python scripts/export_axolotl.py --dpo --inputs datasets/canonical/dpo_v0.6.jsonl datasets/canonical/dpo_v0.7.jsonl --output /tmp/axo_dpo.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agentmujo_training.training.format import sample_to_text


def export_sft(inp: Path, out: Path, limit: int = 0) -> int:
    n = 0
    with inp.open(encoding="utf-8") as fin, out.open("w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            fout.write(json.dumps({"text": sample_to_text(row)}, ensure_ascii=False) + "\n")
            n += 1
            if limit and n >= limit:
                break
    return n


def export_dpo(inputs: list[Path], out: Path, limit: int = 0) -> int:
    n = 0
    with out.open("w", encoding="utf-8") as fout:
        for inp in inputs:
            with inp.open(encoding="utf-8") as fin:
                for line in fin:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    if not row.get("prompt") or not row.get("chosen") or not row.get("rejected"):
                        continue
                    fout.write(json.dumps(
                        {"prompt": row["prompt"], "chosen": row["chosen"],
                         "rejected": row["rejected"]}, ensure_ascii=False) + "\n")
                    n += 1
                    if limit and n >= limit:
                        return n
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sft", action="store_true")
    ap.add_argument("--dpo", action="store_true")
    ap.add_argument("--input", default="")
    ap.add_argument("--inputs", nargs="*", default=[])
    ap.add_argument("--output", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if a.sft:
        n = export_sft(Path(a.input), Path(a.output), a.limit)
    elif a.dpo:
        n = export_dpo([Path(p) for p in a.inputs], Path(a.output), a.limit)
    else:
        ap.error("treba --sft ili --dpo")
    print(f"napisano redova: {n} -> {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
