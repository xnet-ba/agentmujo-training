#!/usr/bin/env python3
"""Proba MERGED tezina (bez adaptera): isti protokol kao probe_lumi (nonthink).
Upotreba: python probe_merged.py <merged-dir> <out.json>
"""
import json
import os
import sys
import torch

sys.path.insert(0, "/scratch/project_465003647/agentmujo/repo/src")

from transformers import AutoModelForCausalLM, AutoTokenizer
from agentmujo_training.agent.loop import SYSTEM, parse_call

MERGED, OUT = sys.argv[1], sys.argv[2]
PROMPTS = [
    "Da li je nginx servis trenutno aktivan?",
    "Prikaži zadnjih 20 linija nginx loga.",
    "Ko slusa na portu 22?",
]

tok = AutoTokenizer.from_pretrained(MERGED, trust_remote_code=False)
model = AutoModelForCausalLM.from_pretrained(
    MERGED, dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
model.eval()


def gen(prompt, max_new=200):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}]
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
    res.append({"prompt": p, "status": st, "tool": tool, "args": args,
                "text": t[:1500]})
    print(f"{st} [{tool}] :: {t[:150]!r}", flush=True)
json.dump(res, open(OUT, "w"), ensure_ascii=False)
