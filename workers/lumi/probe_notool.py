#!/usr/bin/env python3
"""No-tool proba adaptera: chitchat ne smije proizvesti poziv alata.
Upotreba: python probe_notool.py <adapter-dir> <out.json>
"""
import json
import os
import sys
import torch

sys.path.insert(0, "/scratch/project_465003647/agentmujo/repo/src")

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from agentmujo_training.agent.loop import SYSTEM, parse_call

BASE = "Qwen/Qwen3.5-9B"
ADAPTER, OUT = sys.argv[1], sys.argv[2]

PROMPTS = [
    "Čemu služe systemd servisi u Linuxu?",
    "Zahvaljujem, to bi bilo sve!",
    "Objasni mi ukratko čemu služi DNS.",
    "Laku noć, vidimo se sutra!",
]

tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
base = AutoModelForCausalLM.from_pretrained(
    BASE, dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
model = PeftModel.from_pretrained(base, ADAPTER)
model.eval()


def gen(prompt, max_new=200):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}]
    if os.environ.get("PROBE_THINKING", "0") == "1":
        text_in = tok.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True)
    else:
        try:
            text_in = tok.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=True,
                enable_thinking=False)
        except TypeError:
            text_in = tok.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=True)
    inp = tok([text_in], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=max_new, temperature=0.0,
                             do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)


res = []
for p in PROMPTS:
    t = gen(p)
    tool, args, st = parse_call(t)
    ok = st == "none" and "<tool_call>" not in t and '"tool"' not in t
    res.append({"prompt": p, "ok": ok, "status": st, "text": t[:1000]})
    print(f"{'OK ' if ok else 'FAIL'} [{st}] :: {t[:110]!r}", flush=True)
score = sum(1 for r in res if r["ok"])
print(f"\nNO-TOOL SCORE: {score}/{len(res)}")
json.dump({"score": [score, len(res)], "results": res},
          open(OUT, "w"), ensure_ascii=False)
