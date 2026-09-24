#!/usr/bin/env python3
"""Generira Kaggle merge+quant notebook (CPU+RAM, bez treninga).

Slucaj: adapter postoji, ali Oracle nema ~15 GB za 4B merge.
Notebook: baza sa Huba + adapter iz input kernela -> merge bf16 ->
GGUF F16 --no-mtp -> Q8_0 + manifest. Izlaz u /kaggle/working (auto-capture).

Upotreba: python workers/kaggle/make_merge_notebook.py --base-repo ... --base-rev ... \
  --adapter-glob "*/outputs/adapter" --out-name model-q8.gguf \
  --kernel-id admiragic/qwen35-4b-mq01 --input-kernels admiragic/qwen35-4b-joint02 \
  --out-dir /tmp/kaggle_4b_mq01
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-repo", required=True)
    ap.add_argument("--base-rev", required=True)
    ap.add_argument("--adapter-glob", default="*/outputs/adapter")
    ap.add_argument("--out-name", default="model-q8.gguf")
    ap.add_argument("--llamacpp-ref", default="87f9c82",
                    help="pinovana llama.cpp revizija (master puca na Sequence pre-tokenizer)")
    ap.add_argument("--kernel-id", required=True)
    ap.add_argument("--input-kernels", default="")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [
            f"# Merge+Quant — {a.kernel_id}\n",
            "\nBaza sa Huba (pinovana revizija) + LoRA adapter iz input kernela "
            "-> merge bf16 -> GGUF F16 --no-mtp -> Q8_0. Bez tajni u notebooku."]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 0. Dependencies (torch/CUDA se NE reinstaliraju)\n",
            "!pip install -q --upgrade transformers>=4.57 peft>=0.12 safetensors huggingface-hub gguf accelerate torchao>=0.16\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 1. Baza (pin) + adapter (input kernel glob)\n",
            "import glob\n",
            f"BASE_REPO = {a.base_repo!r}\n",
            f"BASE_REV = {a.base_rev!r}\n",
            "from huggingface_hub import snapshot_download\n",
            "base = snapshot_download(BASE_REPO, revision=BASE_REV,\n",
            "    allow_patterns=['*.safetensors', '*.json', '*.jinja', 'tokenizer*', 'vocab*', 'merges*'])\n",
            "print('baza:', base)\n",
            f"cands = sorted(glob.glob('/kaggle/input/**/{a.adapter_glob}', recursive=True))\n",
            "cands = [c for c in cands if __import__('pathlib').Path(c, 'adapter_config.json').exists()]\n",
            "assert cands, 'adapter nije pronadjen u /kaggle/input'\n",
            "print('adapter:', cands[0])\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 2. Merge bf16 (CPU, treba RAM — zato GPU sesija)\n",
            "import shutil as _sh\n",
            "print('disk /tmp:', _sh.disk_usage('/tmp'))\n",
            "import subprocess as _sp\n",
            "print(_sp.run(['free', '-g'], capture_output=True, text=True).stdout)\n",
            "import torch, transformers, peft\n",
            "print('vers:', torch.__version__, transformers.__version__, peft.__version__)\n",
            "from transformers import AutoModelForCausalLM, AutoTokenizer\n",
            "from peft import PeftModel\n",
            "base_m = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16,\n",
            "    device_map='cpu', trust_remote_code=True)\n",
            "model = PeftModel.from_pretrained(base_m, cands[0])\n",
            "merged = model.merge_and_unload()\n",
            "merged.save_pretrained('/tmp/merged')\n",
            "AutoTokenizer.from_pretrained(base, trust_remote_code=True).save_pretrained('/tmp/merged')\n",
            "print('merge gotov')\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 3. llama.cpp (pinovana revizija — master puca na Sequence pre-tokenizer) + konverzija F16 --no-mtp\n",
            "# gguf paket dolazi iz pinovane llama.cpp revizije (PYTHONPATH), ne sa mastera\n",
            "import sys as _sys\n",
            "_sys.path.insert(0, '/tmp/llama.cpp/gguf-py')\n",
            "import os as _os\n",
            "_os.environ['PYTHONPATH'] = '/tmp/llama.cpp/gguf-py:' + _os.environ.get('PYTHONPATH', '')\n",
            "!git clone -q https://github.com/ggerganov/llama.cpp.git /tmp/llama.cpp\n",
            "!cd /tmp/llama.cpp && git checkout -q " + a.llamacpp_ref + " && git log --oneline -1\n",
            "!cd /tmp/llama.cpp && git checkout -q " + a.llamacpp_ref + "\n",
            "!cmake -S /tmp/llama.cpp -B /tmp/llama.cpp/build -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release > /dev/null\n",
            "!cmake --build /tmp/llama.cpp/build --config Release -j $(nproc) --target llama-quantize 2>&1 | tail -1\n",
            "!python3 /tmp/llama.cpp/convert_hf_to_gguf.py /tmp/merged --outfile /tmp/model-f16.gguf --outtype f16 --no-mtp 2>&1 | tail -1\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 4. Q8_0 + manifest (block_count provjera + SHA)\n",
            f"! /tmp/llama.cpp/build/bin/llama-quantize /tmp/model-f16.gguf /kaggle/working/{a.out_name} Q8_0 2>&1 | tail -1\n",
            "import struct, hashlib, json, datetime\n",
            "blob = open('/tmp/model-f16.gguf','rb').read(8000000)\n",
            "key = b'qwen35.block_count'\n",
            "i = blob.find(key)\n",
            "ln = struct.unpack_from('<Q', blob, i-8)[0]\n",
            "p = i + len(key)\n",
            "val = struct.unpack_from('<I', blob, p+4)[0]\n",
            "print('block_count =', val)\n",
            f"h = hashlib.sha256(open('/kaggle/working/{a.out_name}','rb').read()).hexdigest()\n",
            "man = {'base_repo': BASE_REPO, 'base_rev': BASE_REV, 'adapter': cands[0],\n",
            f"       'out': {a.out_name!r}, 'quant': 'Q8_0', 'no_mtp': True, 'block_count': val,\n",
            "       'sha256': h, 'date': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n",
            "open('/kaggle/working/MANIFEST.json','w').write(json.dumps(man, indent=2))\n",
            "print('sha256:', h[:16], '...')\n",
            "print('GOTOVO')\n",
        ]},
        {"cell_type": "markdown", "metadata": {}, "source": [
            "Artefakti u /kaggle/working (auto-capture): "
            f"`{a.out_name}`, `MANIFEST.json`. Fetch na Oracle + Hub upload."]},
    ]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"}, "accelerator": "GPU"},
          "cells": cells}
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "qwen35_merge.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    inputs = [k.strip() for k in a.input_kernels.split(",") if k.strip()]
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": a.kernel_id, "title": a.kernel_id.split("/")[-1],
        "code_file": "qwen35_merge.ipynb", "language": "python",
        "kernel_type": "notebook", "is_private": True,
        "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [],
        "kernel_sources": inputs,
    }, indent=2))
    import ast
    for i, c in enumerate(cells):
        if c["cell_type"] != "code":
            continue
        lines = [ln for ln in c["source"]
                 if not ln.lstrip().startswith(("%", "!"))]
        if "".join(lines).strip():
            ast.parse("".join(lines))
    print(f"OK: {out}/qwen35_merge.ipynb + kernel-metadata.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
