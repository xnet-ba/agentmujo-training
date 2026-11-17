#!/usr/bin/env python3
"""Dodaj trimmed-32k Qwen3.5 vocab hash u llama.cpp konverter (idempotentno).

Problem: trimmed baze (alphaedge-ai/Qwen3.5-*-bos-32768) imaju drugaciji
token-ID hash od upstream Qwen3.5 pa convert_hf_to_gguf.py puca sa
"NotImplementedError: BPE pre-tokenizer was not recognized".
Split regex je identican upstreamu (razlika samo trim_offsets) pa je mapiranje
na "qwen35" korektno, ne hack.

Upotreba: python quantization/patch_llamacpp_vocab.py <llama.cpp-dir> [jos-hashova...]
Poziva se iz gguf.sbatch prije convert koraka (samo za trimmed baze).
"""
from __future__ import annotations

import sys
from pathlib import Path

# hash -> (ggml pre, komentar); hash = sha256(str(tokenizer.encode(chktxt)))
KNOWN = {
    "3307159a20fcb0208cc6fbe0a7adbb882d8ab464496cd3adadabc897f1b2496c":
        ("qwen35", "alphaedge-ai/Qwen3.5-2B-bos-32768 (trimmed 32k)"),
}


def main() -> int:
    if len(sys.argv) < 2:
        print(f"upotreba: {sys.argv[0]} <llama.cpp-dir>")
        return 2
    extra = sys.argv[2:]
    base = Path(sys.argv[1]) / "conversion" / "base.py"
    s = base.read_text(encoding="utf-8")
    added = 0
    for h in list(KNOWN) + extra:
        if h in s:
            continue
        pre, _ = KNOWN.get(h, ("qwen35", "rucno dodan hash"))
        anchor = '            res = "qwen35"\n'
        assert anchor in s, "llama.cpp base.py format se promijenio!"
        s = s.replace(anchor, anchor +
                      f'        if chkhsh == "{h}":\n'
                      f'            # trimmed vocab ({pre})\n'
                      f'            res = "{pre}"\n', 1)
        added += 1
    if added:
        base.write_text(s, encoding="utf-8")
    print(f"vocab-patch: {added} novih, dir={sys.argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
