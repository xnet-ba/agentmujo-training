"""Dry-run validacija Benchmark Laba bez GPU-a (vrijeme: ~10 s)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_tasks_bosnian_200():
    sys.path.insert(0, str(REPO / "workers/kaggle/benchmark_lab"))
    from tasks_bosnian import build_samples
    s = build_samples(200)
    assert len(s) == 200, len(s)
    assert sum(1 for x in s if x["podgrupa"] == "ijekavica") == 100
    assert sum(1 for x in s if x["podgrupa"] == "znanje-bs") == 100


def test_tasks_fc_cita_cases():
    sys.path.insert(0, str(REPO / "workers/kaggle/benchmark_lab"))
    from tasks_fc import load_fc_cases
    cases = load_fc_cases(REPO / "benchmark/cases_v0.5.jsonl")
    assert len(cases) >= 30, len(cases)


def test_notebook_gen(tmp_path=None):
    out = REPO / "workers/kaggle/benchmark_lab/_dryrun"
    r = subprocess.run([sys.executable,
                        str(REPO / "workers/kaggle/benchmark_lab/make_bench_notebook.py"),
                        "--out-dir", str(out), "--limit", "5"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]
    nb = json.loads((out / "bench_lab.ipynb").read_text())
    assert nb["nbformat"] == 4 and len(nb["cells"]) == 5
    # pocisti
    import shutil
    shutil.rmtree(out, ignore_errors=True)
