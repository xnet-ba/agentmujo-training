#!/usr/bin/env python3
"""Generira samostalni eval notebook: baza + LoRA adapter sa prethodnog
Kaggle kernel outputa -> AgentMujo-Bench v0.3 -> eval_report.json.

Upotreba: python workers/kaggle/make_eval_notebook.py <train-job-id> \
  --cases benchmark/cases_v0.5.jsonl --out-dir /tmp/kaggle_eval \
  --kernel-id admiragic/qwen35-fc-eval --input-kernel admiragic/qwen35-fc-dev
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--cases", default="benchmark/cases_v0.5.jsonl")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--kernel-id", default="admiragic/qwen35-fc-eval")
    ap.add_argument("--input-kernel", default="admiragic/qwen35-fc-dev")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--think", action="store_true",
                    help="eval u thinking rezimu (think=true, vise tokena)")
    a = ap.parse_args()

    think_flag = "True" if a.think else "False"
    max_tok = a.max_tokens * (2 if a.think else 1)
    gen_cell = "\n".join([
        "# 3. Eval: baza + adapter -> bench -> eval_report.json",
        f"# REZIM: {'THINKING' if a.think else 'NON-THINKING'}",
        "import glob, json, re, sys, time",
        "sys.path.insert(0, 'agentmujo-training/src')",
        "from agentmujo_training.benchmark.runner import load_cases, score_prediction",
        "import torch",
        "from transformers import AutoModelForCausalLM, AutoTokenizer",
        "from peft import PeftModel",
        "BASE = 'alphaedge-ai/Qwen3.5-2B-bos-32768'",
        "SYSTEM = ('Ti si AgentMujo, asistent za administraciju Linux servera. '",
        "          'Odgovaraj na bosanskom jeziku (ijekavica). '",
        "          'Ako zadatak zahtijeva alat, odgovori KANONSKIM formatom: '",
        "          '<tool_call><function=ime><parameter=arg>vrijednost</parameter></function></tool_call>.')",
        "hits = glob.glob('/kaggle/input/**/adapter_model.safetensors', recursive=True)",
        "assert hits, 'adapter nije pronadjen u /kaggle/input'",
        "# Prioritet: finalni outputs/adapter, pa ne-checkpoint, pa bilo koji",
        "final = [h for h in hits if '/outputs/adapter/' in h]",
        "nonckpt = [h for h in hits if '/checkpoints/' not in h]",
        "ADAPTER = str(__import__('pathlib').Path((final or nonckpt or hits)[0]).parent)",
        "print('adapter:', ADAPTER)",
        "tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)",
        "base = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16,",
        "    device_map='auto', trust_remote_code=True)",
        "model = PeftModel.from_pretrained(base, ADAPTER)",
        "model.eval()",
        "FUNC_RE = re.compile(r'<function=([a-z_][a-z0-9_]*)>', re.IGNORECASE)",
        "PARAM_RE = re.compile(r'<parameter=([a-z_][a-z0-9_]*)>(.*?)</parameter>', re.IGNORECASE | re.DOTALL)",
        "results = []",
        f"cases = load_cases('agentmujo-training/{a.cases}')",
        "t0 = time.time()",
        "with torch.no_grad():",
        "    for c in cases:",
        "        prompt = tok.apply_chat_template(",
        "            [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': c.prompt}],",
        f"            tokenize=False, add_generation_prompt=True, enable_thinking={think_flag}),",
        "        if not isinstance(prompt, str):  # sablon ponekad vrati listu",
        "            prompt = tok.decode(prompt) if all(isinstance(x, int) for x in prompt) else ''.join(map(str, prompt))",
        "        inp = tok([prompt], return_tensors='pt').to(model.device)",
        "        out = model.generate(**inp, max_new_tokens=%d, temperature=0.0, do_sample=False," % max_tok,
        "            pad_token_id=tok.eos_token_id)",
        "        text = tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)",
        "        m = FUNC_RE.search(text or '')",
        "        tool, args = (None, None) if not m else (m.group(1), {})",
        "        if m:",
        "            args = {}",
        "            for k, v in PARAM_RE.findall(text):",
        "                v = v.strip()",
        "                args[k] = int(v) if k in ('port', 'lines', 'limit', 'timeout_s') and v.isdigit() else v",
        "        scores = score_prediction(c, tool, args, text)",
        "        trace = [tool]",
        "        if c.must_verify and tool is not None:",
        "            follow = ([{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': c.prompt}]",
        "                + [{'role': 'assistant', 'content': text}]",
        "                + [{'role': 'user', 'content': '<tool_response>\\n{\\'result\\': \\'ok\\'}\\n</tool_response>'}])",
        "            p2 = tok.apply_chat_template(follow, tokenize=False, add_generation_prompt=True)",
        "            inp2 = tok([p2] if isinstance(p2, str) else [''.join(map(str, p2))], return_tensors='pt').to(model.device)",
        "            out2 = model.generate(**inp2, max_new_tokens=128, temperature=0.0, do_sample=False,",
        "                pad_token_id=tok.eos_token_id)",
        "            text2 = tok.decode(out2[0][inp2.input_ids.shape[1]:], skip_special_tokens=True)",
        "            m2 = FUNC_RE.search(text2 or '')",
        "            tool2 = m2.group(1) if m2 else None",
        "            trace.append(tool2)",
        "            if tool2 is not None:",
        "                scores['multi_step'] = 1 if (c.expected_tool in trace) else 0",
        "                if tool2 == c.expected_tool:",
        "                    scores['tool_selection'] = 1",
        "        results.append({'case': c.id, 'tool': tool, 'args': args, 'scores': scores,",
        "                        'trace': trace, 'excerpt': (text or '')[:200]})",
        "        print(f\"[{c.id}] {tool} {scores}\", flush=True)",
        "agg = {}",
        "for r in results:",
        "    for k, v in r['scores'].items():",
        "        agg.setdefault(k, []).append(v)",
        "summary = {k: {'n': len(v), 'mean': round(sum(v) / len(v), 3)} for k, v in sorted(agg.items())}",
        "print(json.dumps(summary, indent=2, ensure_ascii=False))",
        "Path = __import__('pathlib').Path",
        "Path('/kaggle/working/eval_report.json').write_text(",
        "    json.dumps({'job': '%s', 'mode': '%s', 'adapter': ADAPTER, 'summary': summary, 'results': results}," % (a.job_id, 'thinking' if a.think else 'non-thinking'),
        "                 indent=2, ensure_ascii=False))",
        "print(f'vrijeme: {time.time()-t0:.0f}s')",
    ])
    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [
            f"# AgentMujo eval — adapter iz joba `{a.job_id}`\n",
            "\nBench v0.3 nad bazom+adapterom (bf16, greedy). Bez tajni."]},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 0. Repo + dependencies (torch/CUDA se NE reinstaliraju)\n",
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
         "source": gen_cell.splitlines(keepends=True)},
        {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [
            "# 4. eval_report.json ostaje u /kaggle/working (auto-capture).",
        ]},
    ]
    nb = {"nbformat": 4, "nbformat_minor": 5,
          "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                      "name": "python3"}, "accelerator": "GPU"},
          "cells": cells}
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "qwen35_eval.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False))
    (out / "kernel-metadata.json").write_text(json.dumps({
        "id": a.kernel_id, "title": a.kernel_id.split("/")[-1],
        "code_file": "qwen35_eval.ipynb", "language": "python",
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
    print(f"OK: {out}/qwen35_eval.ipynb + kernel-metadata.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
