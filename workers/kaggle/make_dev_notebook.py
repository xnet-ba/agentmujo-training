#!/usr/bin/env python3
"""Generira samostalni Kaggle notebook iz Oracle job direktorija.

Upotreba: python workers/kaggle/make_dev_notebook.py <job_id> --out-dir /tmp/kaggle_dev
Izlaz: qwen35_dev.ipynb + kernel-metadata.json (spremno za `kaggle kernels push`).

Notebook klonira javni GitHub repo (bez kredencijala), upisuje job
config+metadata iz Oracle traga (paritet garantiran), pokreće job_run.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--kernel-id", default="admiragic/qwen35-fc-dev")
    ap.add_argument("--input-kernels", default="",
                    help="zarezom odvojeni kernel inputi, npr. admiragic/qwen35-fc-dev3")
    a = ap.parse_args()

    jdir = REPO / "training" / "jobs" / a.job_id
    config = (jdir / "config.yaml").read_text(encoding="utf-8")
    metadata = (jdir / "metadata.json").read_text(encoding="utf-8")

    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [
            f"# AgentMujo dev SFT — job `{a.job_id}`\n",
            "\nOracle trag + GitHub repo (javan, bez kredencijala). "
            "Baza i dataset direktno sa Huba. Bez tajni u notebooku."]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 0. Repo + dependencies (torch/CUDA se NE reinstaliraju)\n",
            "!git clone -q https://github.com/xnet-ba/agentmujo-training.git\n",
            "%pip install -q --upgrade transformers>=4.57 datasets>=3.0 peft>=0.12 trl>=0.12 accelerate>=0.33 bitsandbytes>=0.43 torchao>=0.16 huggingface-hub safetensors pyyaml\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 0b. Version gate\n",
            "import transformers\n",
            "print('transformers:', transformers.__version__)\n",
            "from transformers import AutoConfig\n",
            "try:\n",
            "    AutoConfig.for_model('qwen3_5')\n",
            "    print('PASS qwen3_5-podrska')\n",
            "except KeyError:\n",
            "    raise SystemExit('STOP: transformers prestar za qwen3_5')\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 1. GPU preflight\n",
            "import torch\n",
            "assert torch.cuda.is_available(), 'nema GPU — STOP'\n",
            "print('GPU:', torch.cuda.get_device_name(0), '| CUDA:', torch.version.cuda)\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 2. Job spec sa Oraclea (paritet, ne prepisivanje)\n",
            "from pathlib import Path\n",
            f"JOB_ID = {a.job_id!r}\n",
            "CONFIG = r''' " + config.replace("\\", "\\\\") + "'''\n",
            "META = r''' " + metadata.replace("\\", "\\\\") + "'''\n",
            "jdir = Path('agentmujo-training') / 'training' / 'jobs' / JOB_ID\n",
            "jdir.mkdir(parents=True, exist_ok=True)\n",
            "(jdir / 'config.yaml').write_text(CONFIG)\n",
            "(jdir / 'metadata.json').write_text(META)\n",
            "(jdir / 'README.md').write_text(f'# Job {JOB_ID} (Kaggle worker)\\n')\n",
            "print('job spec zapisan:', jdir)\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 3. Trening (teška ćelija: desetine minuta na T4)\n",
            "%cd agentmujo-training\n",
            f"!python workers/kaggle/job_run.py --job-dir training/jobs/{a.job_id}\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 4. Artefakti ostaju u /kaggle/working (auto-capture):\n",
            "#    training/jobs/<id>/outputs/{status,metrics,manifest}.json + adapter/\n",
            "#    Vidi docs/KAGGLE_WORKER.md za fetch + resume.",
        ]},
    ]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"}, "accelerator": "GPU"},
          "cells": cells}
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "qwen35_dev.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    inputs = [k.strip() for k in a.input_kernels.split(",") if k.strip()]
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": a.kernel_id, "title": a.kernel_id.split("/")[-1],
        "code_file": "qwen35_dev.ipynb", "language": "python",
        "kernel_type": "notebook", "is_private": True,
        "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [],
        "kernel_sources": inputs,
    }, indent=2))
    # sintaksna provjera code ćelija
    import ast
    for i, c in enumerate(cells):
        if c["cell_type"] != "code":
            continue
        lines = [ln for ln in c["source"]
                 if not ln.lstrip().startswith(("%", "!"))]
        if "".join(lines).strip():
            ast.parse("".join(lines))
    print(f"OK: {out}/qwen35_dev.ipynb + kernel-metadata.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
