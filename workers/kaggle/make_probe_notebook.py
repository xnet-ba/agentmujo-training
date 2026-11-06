#!/usr/bin/env python3
"""Generira probe notebook: 12 bosanskih promptova nad adapterom.

Upotreba: python workers/kaggle/make_probe_notebook.py --out-dir /tmp/kaggle_probe \
  --kernel-id admiragic/qwen35-probe --input-kernel admiragic/qwen35-joint
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROBE_PROMPTS = [
    ("bp-01", "Objasni ukratko šta je fotosinteza."),
    ("bp-02", "Napiši kratku čestitku za rođendan na bosanskom jeziku."),
    ("bp-03", "Koja je razlika između riječi 'vrijeme' i 'vrijednost'?"),
    ("bp-04", "Prevedi na bosanski jezik: 'The server needs more memory.'"),
    ("bp-05", "Objasni djetetu šta je internet."),
    ("bp-06", "Sastavi tri rečenice sa riječju 'mlijeko'."),
    ("bp-07", "Šta znači riječ 'džep'?"),
    ("bp-08", "Napiši kratku vijest o vremenskoj prognozi za Sarajevo."),
    ("bp-09", "Objasni razliku između 'da li' i 'je li' u bosanskom jeziku."),
    ("bp-10", "Sažmi u dvije rečenice: 'Linux je porodica operativnih sistema otvorenog koda koju je započeo Linus Torvalds. Danas pokreće većinu servera, superračunara i Android telefona.'"),
    ("bp-11", "Koji padež je upotrijebljen u rečenici 'Vidim kuću'?"),
    ("bp-12", "Napiši kratko uputstvo za kuhanje kafe na bosanskom jeziku."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--kernel-id", default="admiragic/qwen35-probe")
    ap.add_argument("--input-kernel", required=True)
    a = ap.parse_args()

    gen = "\n".join([
        "# 2. Proba: 12 bosanskih promptova -> probe_report.json",
        "import glob, json, time",
        "import torch",
        "from transformers import AutoModelForCausalLM, AutoTokenizer",
        "from peft import PeftModel",
        "BASE = 'alphaedge-ai/Qwen3.5-2B-bos-32768'",
        "SYSTEM = 'Ti si koristan asistent. Odgovaraj uvijek na bosanskom jeziku (ijekavica).'",
        "PROMPTS = " + json.dumps(PROBE_PROMPTS, ensure_ascii=False),
        "hits = glob.glob('/kaggle/input/**/adapter_model.safetensors', recursive=True)",
        "final = [h for h in hits if '/outputs/adapter/' in h]",
        "nonckpt = [h for h in hits if '/checkpoints/' not in h]",
        "ADAPTER = str(__import__('pathlib').Path((final or nonckpt or hits)[0]).parent)",
        "print('adapter:', ADAPTER)",
        "tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)",
        "base = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16,",
        "    device_map='auto', trust_remote_code=True)",
        "model = PeftModel.from_pretrained(base, ADAPTER)",
        "model.eval()",
        "results = []",
        "t0 = time.time()",
        "with torch.no_grad():",
        "    for pid, prompt in PROMPTS:",
        "        text_in = tok.apply_chat_template(",
        "            [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt}],",
        "            tokenize=False, add_generation_prompt=True)",
        "        inp = tok([text_in], return_tensors='pt').to(model.device)",
        "        out = model.generate(**inp, max_new_tokens=300, temperature=0.7, do_sample=True,",
        "            pad_token_id=tok.eos_token_id)",
        "        text = tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)",
        "        results.append({'id': pid, 'prompt': prompt, 'text': text})",
        "        print(f'[{pid}] {text[:120]}', flush=True)",
        "Path = __import__('pathlib').Path",
        "Path('/kaggle/working/probe_report.json').write_text(",
        "    json.dumps({'results': results}, indent=2, ensure_ascii=False))",
        "print(f'gotovo za {time.time()-t0:.0f}s')",
    ])
    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [
            "# Bosanska proba (replay provjera)\n\nIsti 12 promptova kao TP-0 proba. Bez tajni."]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 0. Repo + dependencies\n",
            "!git clone -q https://github.com/xnet-ba/agentmujo-training.git\n",
            "%pip install -q --upgrade transformers>=4.57 peft>=0.12 accelerate>=0.33 bitsandbytes>=0.43 torchao>=0.16 huggingface-hub safetensors\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 1. GPU preflight\n",
            "import torch\n",
            "assert torch.cuda.is_available(), 'nema GPU — STOP'\n",
            "print('GPU:', torch.cuda.get_device_name(0))\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
         "source": gen.splitlines(keepends=True)},
    ]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"}, "accelerator": "GPU"},
          "cells": cells}
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "qwen35_probe.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": a.kernel_id, "title": a.kernel_id.split("/")[-1],
        "code_file": "qwen35_probe.ipynb", "language": "python",
        "kernel_type": "notebook", "is_private": True,
        "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [],
        "kernel_sources": [a.input_kernel],
    }, indent=2))
    import ast
    for i, c in enumerate(cells):
        if c["cell_type"] != "code":
            continue
        lines = [ln for ln in c["source"] if not ln.lstrip().startswith(("%", "!"))]
        if "".join(lines).strip():
            ast.parse("".join(lines))
    print(f"OK: {out}/qwen35_probe.ipynb + kernel-metadata.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
