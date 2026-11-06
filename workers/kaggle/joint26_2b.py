#!/usr/bin/env python3
"""Generira samostalni Kaggle notebook za JOINT-26-2B job iz Oracle job direktorija.

Upotreba: python workers/kaggle/joint26_2b.py <job_id> --out-dir /tmp/kaggle_j26b
Izlaz: qwen35_joint26_2b.ipynb + kernel-metadata.json (spremno za `kaggle kernels push`).
Nikada se NE pusha niti pokrece iz ove sesije (bez trosenja GPU kvote).

Obrazac je isti kao make_dev_notebook.py: Oracle trag + javni GitHub repo
(bez kredencijala), baza i dataset direktno sa Huba, job_run.py izvrsava.
Razlika: defaulti za joint26-2b (kernel id, notebook ime) + zasticena
adapter-upload celija (HF_UPLOAD_REPO iz env/Kaggle Secrets, nikad u notebooku).
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
    ap.add_argument("--kernel-id", default="admiragic/qwen35-joint26-2b")
    ap.add_argument("--notebook", default="qwen35_joint26_2b.ipynb")
    ap.add_argument("--input-kernels", default="",
                    help="zarezom odvojeni kernel inputi (za resume sa adaptera)")
    a = ap.parse_args()

    jdir = REPO / "training" / "jobs" / a.job_id
    config = (jdir / "config.yaml").read_text(encoding="utf-8")
    metadata = (jdir / "metadata.json").read_text(encoding="utf-8")

    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [
            f"# AgentMujo JOINT-26-2B SFT — job `{a.job_id}`\n",
            "\nOracle trag + GitHub repo (javan, bez kredencijala). "
            "Baza i dataset direktno sa Huba (bf16-LoRA, bez 4-bita). Bez tajni u notebooku."]},
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
            "# 3. Trening (teska celija: vise sati na T4, sesija max 12 h)\n",
            "%cd agentmujo-training\n",
            f"!python workers/kaggle/job_run.py --job-dir training/jobs/{a.job_id}\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 4. Adapter -> HF private repo (samo uz HF_UPLOAD_REPO iz env/Secrets;\n",
            "#    token nikad u notebooku; preskoci ako nije postavljen)\n",
            "import os\n",
            "repo = os.environ.get('HF_UPLOAD_REPO', '')\n",
            f"ad = 'agentmujo-training/training/jobs/{a.job_id}/outputs/adapter'\n",
            "if repo:\n",
            "    print('upload:', ad, '->', repo)\n",
            "else:\n",
            "    print('SKIP upload (HF_UPLOAD_REPO nije postavljen)')\n",
            "!test -n \"$HF_UPLOAD_REPO\" && hf upload \"$HF_UPLOAD_REPO\" \""
            f"agentmujo-training/training/jobs/{a.job_id}/outputs/adapter\""
            " --repo-type model --private || true\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 5. Artefakti ostaju u /kaggle/working (auto-capture):\n",
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
    (out / a.notebook).write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    inputs = [k.strip() for k in a.input_kernels.split(",") if k.strip()]
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": a.kernel_id, "title": a.kernel_id.split("/")[-1],
        "code_file": a.notebook, "language": "python",
        "kernel_type": "notebook", "is_private": True,
        "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [],
        "kernel_sources": inputs,
    }, indent=2))
    # sintaksna provjera code celija
    import ast
    for i, c in enumerate(cells):
        if c["cell_type"] != "code":
            continue
        lines = [ln for ln in c["source"]
                 if not ln.lstrip().startswith(("%", "!"))]
        if "".join(lines).strip():
            ast.parse("".join(lines))
    print(f"OK: {out}/{a.notebook} + kernel-metadata.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
