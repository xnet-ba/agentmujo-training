#!/usr/bin/env python3
"""Ciljani binarni patch GGUF metapodataka (bez diranja tenzora).

Slucaj: llama.cpp konverter za qwen3_5 upise block_count=25 (uracunat MTP
sloj) dok tenzora ima za 24 bloka — Ollama/Ollama-runner odbija fajl
(`blk.24.attn_norm.weight not found`). Referentni ispravni Q8 ima 24.

Upotreba: python quantization/patch_gguf.py model.gguf --set-qwen35-block-count 24
Radi in-place kopiju na --output (default: prepisuje uz .bak).
"""
from __future__ import annotations

import argparse
import shutil
import struct
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--output", default=None)
    ap.add_argument("--set-qwen35-block-count", type=int, required=True)
    a = ap.parse_args()

    out = Path(a.output) if a.output else Path(a.input)
    if out == Path(a.input) and a.output is None:
        bak = Path(str(a.input) + ".bak")
        shutil.copy2(a.input, bak)
        print(f"[patch] backup: {bak}")
    elif a.output and Path(a.output) != Path(a.input):
        shutil.copy2(a.input, a.output)

    key = b"qwen35.block_count"
    with open(out, "r+b") as f:
        blob = bytearray(f.read())
        i = blob.find(key)
        assert i != -1, "kljuc nije pronadjen"
        # GGUF KV: u64 len + key bytes + u32 type + u32 value
        ln = struct.unpack_from("<Q", blob, i - 8)[0]
        assert ln == len(key), f"los format (len={ln})"
        p = i + len(key)
        typ = struct.unpack_from("<I", blob, p)[0]
        assert typ == 4, f"ocekivan uint32 (4), nadjen {typ}"
        old = struct.unpack_from("<I", blob, p + 4)[0]
        struct.pack_into("<I", blob, p + 4, a.set_qwen35_block_count)
        f.seek(0)
        f.write(blob)
    print(f"[patch] qwen35.block_count: {old} -> {a.set_qwen35_block_count} ({out})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
