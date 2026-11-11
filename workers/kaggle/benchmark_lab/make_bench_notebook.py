#!/usr/bin/env python3
"""Generira Kaggle Benchmark Lab notebook (kagyl-gpu-tester).

Jedan kernel: skine Q8 GGUF -> digne llama.cpp OpenAI server ->
Inspect AI (5 standardnih + bosanski 200 + FC bench) ->
pandas agregacija -> results.csv + bench_report.html u /kaggle/working.

Upotreba:
  python workers/kaggle/benchmark_lab/make_bench_notebook.py \
    --out-dir /tmp/kaggle_bench --limit 100 \
    [--model-b-repo REPO --model-b-file FILE --model-b-label LABEL]

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
# 3. Model server (Ollama + GGUF, OpenAI-kompatibilan) + Inspect evals
import os, subprocess, time, json
import urllib.request

GGUF_REPO = "__GGUF_REPO__"
GGUF_FILE = "__GGUF_FILE__"  # pin iz bench_lab.json; novi model = novi fajl
MODEL_B_REPO = "__MODEL_B_REPO__"  # prazno = samo tuned (politika poslije baselinea)
MODEL_B_FILE = "__MODEL_B_FILE__"
MODEL_B_LABEL = "__MODEL_B_LABEL__"

from huggingface_hub import hf_hub_download
import shutil
MODELS = {"tuned": (GGUF_REPO, GGUF_FILE)}
if MODEL_B_REPO:
    MODELS[MODEL_B_LABEL or "challenger"] = (MODEL_B_REPO, MODEL_B_FILE)
local = {}
for k, (repo, fn) in MODELS.items():
    p = hf_hub_download(repo, fn, local_dir="/tmp/models/%s" % k)
    local[k] = p  # /tmp, ne /kaggle/working — GGUF (10-20 GB) ne smije u output
    print(k, "->", p, flush=True)

# server: Ollama binarni release (install.sh puca na Kaggleu — v6 dokaz).
# Verzija preko GitHub API-ja (prazno = latest); pinovati nakon prvog zelenog runa.
OLLAMA_VER = "__OLLAMA_VER__"
import json as _json
if not OLLAMA_VER:
    _req = urllib.request.Request("https://api.github.com/repos/ollama/ollama/releases/latest",
                                  headers={"User-Agent": "bench-lab"})
    OLLAMA_VER = _json.load(urllib.request.urlopen(_req, timeout=30))["tag_name"]
print("ollama:", OLLAMA_VER, flush=True)
_tgz = "/tmp/ollama-linux-amd64.tar.zst"
_url = "https://github.com/ollama/ollama/releases/download/" + OLLAMA_VER + "/ollama-linux-amd64.tar.zst"
subprocess.run(["bash", "-lc", "curl -sSL " + _url + " -o " + _tgz], check=True)
import zstandard as _zstd, tarfile  # Kaggle nema zstd binaru (v8 dokaz) — pure-python put
_dctx = _zstd.ZstdDecompressor()
with open(_tgz, "rb") as _fh, _dctx.stream_reader(_fh) as _sr, tarfile.open(fileobj=_sr, mode="r|") as _tf:
    _tf.extractall("/tmp")
os.remove(_tgz)
subprocess.run(["/tmp/bin/ollama", "--version"], check=True)
OLLAMA = "/tmp/bin/ollama"
ollog = open("/kaggle/working/ollama.log", "w")
subprocess.Popen([OLLAMA, "serve"], stdout=ollog, stderr=subprocess.STDOUT)
os.environ["OPENAI_BASE_URL"] = "http://127.0.0.1:11434/v1"
os.environ["OPENAI_API_KEY"] = "ollama"

def ollama_up():
    for _ in range(30):
        time.sleep(10)
        try:
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
            if urllib.request.urlopen(req, timeout=5).status == 200:
                print("ollama OK", flush=True)
                return
        except Exception:
            print("cekanje ollame...", flush=True)
    raise RuntimeError("ollama se nije digla (vidi ollama.log)")

def ensure_model(name, gguf):
    open("/kaggle/working/Modelfile", "w").write("FROM %s\n" % gguf)
    r = subprocess.run([OLLAMA, "create", name, "-f", "/kaggle/working/Modelfile"],
                       capture_output=True, text=True)
    print((r.stdout + r.stderr)[-300:], flush=True)
    if r.returncode != 0:
        raise RuntimeError("ollama create fail: " + (r.stderr or "")[-500:])

ollama_up()

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
TASKS = {"mmlu_pro": mmlu_pro, "gsm8k": gsm8k, "arc": arc_challenge,
         "ifeval": ifeval, "gpqa": gpqa_diamond, "bosnian": bosnian_bench,
         "fc": lambda: fc_bench("agentmujo-training/benchmark/cases_v0.5.jsonl")}

all_rows = []
for name, path in local.items():
    ensure_model(name, path)
    t0 = time.time()
    for tname, mk in TASKS.items():
        logs = inspect_eval(mk(), model="openai/" + name, limit=LIMIT if tname != "bosnian" else 200,
                            log_dir=f"/kaggle/working/logs-{name}")
        sc = logs[0].results.scores[0].metrics if logs and logs[0].results and logs[0].results.scores else {}
        acc = sc.get("accuracy", {}).get("value", None) if isinstance(sc, dict) else None
        all_rows.append({"model": name, "task": tname, "score": acc,
                         "secs": round(time.time() - t0, 1), "gpu_mem_gb": gpu_mem_gb()})
        print(f"[{name}/{tname}] {acc}", flush=True)

# 3c. DeepInfra baseline (samo uz Kaggle secret + zadan model; inace skip = 0 troska)
DI_MODEL = "__DI_MODEL__"
if DI_MODEL:
    try:
        from kaggle_secrets import UserSecretsClient
        _dikey = UserSecretsClient().get_secret("DEEPINFRA_API_KEY")
    except Exception:
        _dikey = None
        print("nema DEEPINFRA_API_KEY secreta — skip DeepInfra (0 troska)")
    if _dikey:
        from inspect_ai.model import get_model as _gm
        _di = _gm("openai/" + DI_MODEL, base_url="https://api.deepinfra.com/v1/openai", api_key=_dikey)
        _t0 = time.time()
        for tname, mk in TASKS.items():
            _logs = inspect_eval(mk(), model=_di, limit=LIMIT if tname != "bosnian" else 200,
                                 log_dir="/kaggle/working/logs-deepinfra")
            _sc = _logs[0].results.scores[0].metrics if _logs and _logs[0].results and _logs[0].results.scores else {}
            _acc = _sc.get("accuracy", {}).get("value", None) if isinstance(_sc, dict) else None
            all_rows.append({"model": "deepinfra:" + DI_MODEL, "task": tname, "score": _acc,
                             "secs": round(time.time() - _t0, 1), "gpu_mem_gb": 0.0})
            print(f"[deepinfra/{tname}] {_acc}", flush=True)

import pandas as pd
df = pd.DataFrame(all_rows)
df.to_csv("/kaggle/working/bench_results.csv", index=False)
print(df.to_string())
import shutil
shutil.rmtree("/tmp/models", ignore_errors=True)  # oslobodi disk; u outputu ostaju csv/html/png/logovi
print("modeli obrisani; ostaju csv/html/png + logovi")
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--model-b-repo", default="")
    ap.add_argument("--model-b-file", default="")
    ap.add_argument("--model-b-label", default="challenger",
                    help="duel: drugi model u istom kernelu (npr. 4b-dpo01)")
    ap.add_argument("--ollama-ver", default="v0.40.16",
                    help="pin Ollama verzije (default v0.40.16, verificirano 2026-11-11)")
    ap.add_argument("--deepinfra-model", default="",
                    help="baseline preko DeepInfra (npr. Qwen/Qwen3.5-9B); prazno = skip, 0 troska")
    ap.add_argument("--kernel-id", default=CONFIG["kernel_id"])
    ap.add_argument("--gguf-repo", default=CONFIG["gguf_repo"])
    ap.add_argument("--gguf-file", default=CONFIG["gguf_file"],
                    help="novi model = samo promijeni fajl, kernel ostaje isti")
    a = ap.parse_args()

    run_cell = (RUN_CELL.replace("__LIMIT__", str(a.limit))
                .replace("__MODEL_B_REPO__", a.model_b_repo)
                .replace("__MODEL_B_FILE__", a.model_b_file)
                .replace("__MODEL_B_LABEL__", a.model_b_label)
                .replace("__DI_MODEL__", a.deepinfra_model)
                .replace("__OLLAMA_VER__", a.ollama_ver)
                .replace("__GGUF_REPO__", a.gguf_repo)
                .replace("__GGUF_FILE__", a.gguf_file))
    # sve u try/except: traceback se pise u /kaggle/working/ERROR.txt
    # (mali output, moze se skinuti; modeli su u /tmp pa output ostaje lagan)
    run_cell = ("import traceback as _tb\ntry:\n"
                + "\n".join(("    " + ln if ln.strip() else ln)
                             for ln in run_cell.splitlines())
                + "\nexcept Exception:\n"
                + "    open('/kaggle/working/ERROR.txt', 'w').write(_tb.format_exc())\n"
                + "    print(open('/kaggle/working/ERROR.txt').read(), flush=True)\n"
                + "    raise")

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
            "Q8 GGUF → Ollama (CUDA) → Inspect AI (mmlu_pro, gsm8k, arc, ifeval, gpqa, bosnian-200, fc) → CSV/HTML.\n",
            f"Limit po tasku: {a.limit} (bosanski uvijek 200). Model B: {a.model_b_label or '-tuned-only-'}."]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 0. Repo + deps (~6 min prvi put)\n",
            "!git clone -q https://github.com/xnet-ba/agentmujo-training.git\n",
            "%pip install -q inspect-ai inspect-evals pandas matplotlib huggingface-hub zstandard openai>=3.4.0\n",
            "%pip install -q git+https://github.com/josejg/instruction_following_eval.git  # ifeval dep\n",
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
