#!/usr/bin/env python3
"""Generira Kaggle Benchmark Lab notebook (kagyl-gpu-tester).

Jedan kernel: skine Q8 GGUF -> digne llama.cpp OpenAI server ->
Inspect AI (5 standardnih + bosanski 200 + FC bench) ->
pandas agregacija -> results.csv + bench_report.html u /kaggle/working.

Upotreba:
  python workers/kaggle/benchmark_lab/make_bench_notebook.py \
    --out-dir /tmp/kaggle_bench --limit 100 [--compare-base]

Vrijeme generisanja lokalno: ~5 s. Vrijeme izvrsavanja na Kaggle T4:
  ~10 min setup + ~60-90 min eval (1 model, limit 100) po modelu.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

CONFIG = json.loads((Path(__file__).parent / "bench_lab.json").read_text())
# Pravilo (pinovano): baseline poredjenje SAMO jednom, poslije samo tuned.
# Kernel ID se ne smislja rucno — uvijek iz bench_lab.json.

RUN_CELL = r"""
# 3. Model server (llama.cpp, OpenAI-kompatibilan) + Inspect evals
import os, subprocess, time, json, glob
import urllib.request

GGUF_REPO = "__GGUF_REPO__"
GGUF_FILE = "__GGUF_FILE__"  # pin iz bench_lab.json; novi model = novi fajl
BASE_GGUF_REPO = "shaban2024/Qwen3.5-9B-Base-Q8"  # samo uz --compare-base
COMPARE = __COMPARE__

from huggingface_hub import hf_hub_download
MODELS = {"tuned": (GGUF_REPO, GGUF_FILE)}
if COMPARE:
    MODELS["base"] = (BASE_GGUF_REPO, GGUF_FILE)
for k, (repo, fn) in MODELS.items():
    p = hf_hub_download(repo, fn, local_dir="/kaggle/working/models")
    print(k, "->", p, flush=True)

# server na 8000 (jedan model odjednom — T4 ima 16 GB)
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:8000/v1"
os.environ["OPENAI_API_KEY"] = "sk-bench"
os.environ["LLAMA_ARG_N_CTX"] = "4096"

def start_server(gguf_path):
    subprocess.run(["pkill", "-f", "llama_cpp.server"], capture_output=True)
    time.sleep(3)
    log = open("/kaggle/working/llama.log", "w")
    subprocess.Popen(["python", "-m", "llama_cpp.server",
                      "--model", gguf_path, "--port", "8000",
                      "--n_ctx", "4096", "--n_gpu_layers", "-1"],
                     stdout=log, stderr=subprocess.STDOUT)
    for _ in range(60):
        time.sleep(10)
        try:
            r = urllib.request.urlopen("http://127.0.0.1:8000/v1/models", timeout=5)
            if r.status == 200:
                print("server OK:", gguf_path, flush=True)
                return
        except Exception as e:
            print("cekanje servera...", flush=True)
    raise RuntimeError("llama server se nije digao (vidi llama.log)")

# brzina + memorija
import torch
def gpu_mem_gb():
    return round(torch.cuda.memory_allocated() / 1e9, 2) if torch.cuda.is_available() else 0.0

from inspect_ai import eval as inspect_eval
from inspect_evals.mmlu_pro import mmlu_pro
from inspect_evals.gsm8k import gsm8k
from inspect_evals.arc import arc_challenge
from inspect_evals.ifeval import ifeval
from inspect_evals.gpqa import gpqa_diamond
import sys
sys.path.insert(0, "agentmujo-training/workers/kaggle/benchmark_lab")
from tasks_bosnian import bosnian_bench
from tasks_fc import fc_bench

LIMIT = __LIMIT__
TASKS = {"mmlu_pro": mmlu_pro(), "gsm8k": gsm8k(), "arc": arc_challenge(),
         "ifeval": ifeval(), "gpqa": gpqa_diamond(),
         "bosnian": bosnian_bench()(),
         "fc": fc_bench("agentmujo-training/benchmark/cases_v0.5.jsonl")}

all_rows = []
for name, path in [("tuned", "/kaggle/working/models/" + GGUF_FILE)] + \
        ([("base", "/kaggle/working/models/base-" + GGUF_FILE)] if COMPARE else []):
    start_server(path)
    t0 = time.time()
    for tname, t in TASKS.items():
        logs = inspect_eval(t, model="openai/tuned", limit=LIMIT if tname != "bosnian" else 200,
                            log_dir=f"/kaggle/working/logs-{name}")
        sc = logs[0].results.scores[0].metrics if logs and logs[0].results and logs[0].results.scores else {}
        acc = sc.get("accuracy", {}).get("value", None) if isinstance(sc, dict) else None
        all_rows.append({"model": name, "task": tname, "score": acc,
                         "secs": round(time.time() - t0, 1), "gpu_mem_gb": gpu_mem_gb()})
        print(f"[{name}/{tname}] {acc}", flush=True)

import pandas as pd
df = pd.DataFrame(all_rows)
df.to_csv("/kaggle/working/bench_results.csv", index=False)
print(df.to_string())
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--compare-base", action="store_true",
                    help="JEDNOM za baseline; poslije samo tuned (vidi bench_lab.json)")
    ap.add_argument("--kernel-id", default=CONFIG["kernel_id"])
    ap.add_argument("--gguf-repo", default=CONFIG["gguf_repo"])
    ap.add_argument("--gguf-file", default=CONFIG["gguf_file"],
                    help="novi model = samo promijeni fajl, kernel ostaje isti")
    a = ap.parse_args()

    run_cell = (RUN_CELL.replace("__LIMIT__", str(a.limit))
                .replace("__COMPARE__", "True" if a.compare_base else "False")
                .replace("__GGUF_REPO__", a.gguf_repo)
                .replace("__GGUF_FILE__", a.gguf_file))

    report_cell = "\n".join([
        "# 4. Grafovi + HTML izvjestaj",
        "import pandas as pd",
        "df = pd.read_csv('/kaggle/working/bench_results.csv')",
        "import matplotlib; matplotlib.use('Agg')",
        "import matplotlib.pyplot as plt",
        "fig, ax = plt.subplots(figsize=(10, 4))",
        "piv = df.pivot(index='task', columns='model', values='score')",
        "piv.plot(kind='bar', ax=ax); ax.set_ylim(0, 1); ax.set_title('AgentMujo Benchmark Lab')",
        "plt.tight_layout(); plt.savefig('/kaggle/working/bench_chart.png')",
        "html = '<h1>AgentMujo Benchmark Lab</h1>' + df.to_html(index=False) + \"<img src='bench_chart.png'>\"",
        "open('/kaggle/working/bench_report.html', 'w').write(html)",
        "print('OK: bench_results.csv + bench_report.html + bench_chart.png u /kaggle/working')",
    ])

    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [
            "# AgentMujo Benchmark Lab (kagyl-gpu-tester)\n",
            "Q8 GGUF → llama.cpp → Inspect AI (mmlu_pro, gsm8k, arc, ifeval, gpqa, bosnian-200, fc) → CSV/HTML.\n",
            f"Limit po tasku: {a.limit} (bosanski uvijek 200). Compare-base: {a.compare_base}."]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 0. Repo + deps (~6 min prvi put)\n",
            "!git clone -q https://github.com/xnet-ba/agentmujo-training.git\n",
            "%pip install -q llama-cpp-python inspect-ai inspect-evals pandas matplotlib huggingface-hub\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 1. GPU preflight (T4 16 GB, Q8 staje; BF16 NE staje)\n",
            "import torch\n",
            "assert torch.cuda.is_available(), 'nema GPU — STOP'\n",
            "print('GPU:', torch.cuda.get_device_name(0), '| VRAM: %.1f GB' % (torch.cuda.get_device_properties(0).total_memory/1e9))\n",
        ]},
        {"cell_type": "code", "execution_count": None, "metadata": {},
         "source": run_cell.splitlines(keepends=True)},
        {"cell_type": "code", "execution_count": None, "metadata": {},
         "source": [ln + "\n" for ln in report_cell.splitlines()]},
    ]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"}, "accelerator": "GPU"},
          "cells": cells}
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "bench_lab.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": a.kernel_id, "title": a.kernel_id.split("/")[-1],
        "code_file": "bench_lab.ipynb", "language": "python",
        "kernel_type": "notebook", "is_private": True,
        "enable_gpu": True, "enable_internet": True,
        "dataset_sources": [], "competition_sources": [], "kernel_sources": [],
    }, indent=2))
    for i, c in enumerate(cells):
        if c["cell_type"] != "code":
            continue
        code = "".join(c["source"])
        code = "\n".join(ln for ln in code.splitlines()
                          if not ln.lstrip().startswith(("%", "!")))
        if code.strip():
            ast.parse(code)
    print(f"OK: {out}/bench_lab.ipynb")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
