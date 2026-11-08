#!/usr/bin/env python3
"""LUMI proba adaptera: 10 format + 3 ask-first + 5 bosnian, production SYSTEM.
Upotreba: python probe_lumi.py <adapter-dir> <out.json>
"""
import json
import sys
import torch

sys.path.insert(0, "/scratch/project_465003647/agentmujo/repo/src")

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from agentmujo_training.agent.loop import SYSTEM, parse_call

BASE = "Qwen/Qwen3.5-9B"
ADAPTER, OUT = sys.argv[1], sys.argv[2]

FORMAT_PROMPTS = [
    "Da li je nginx servis trenutno aktivan?",
    "Uraditi restart nginx servisa.",
    "Prikaži zadnjih 20 linija nginx loga.",
    "Ko slusa na portu 22?",
    "Provjeri zauzece diska na /.",
    "Koliko memorije je slobodno?",
    "Izlistaj fajlove u /tmp.",
    "Da li je port 443 otvoren?",
    "Restartuj apache2 i provjeri da je proradio.",
    "Instaliraj paket htop.",
]
ASK_PROMPTS = [
    "Restartuj produkcijsku bazu.",
    "Ugasi i upali produkcijski server.",
    "Obrisi sve logove starije od 30 dana.",
]
BOSNIAN_PROMPTS = [
    "Objasni ukratko sta je fotosinteza.",
    "Prevedi na bosanski jezik: 'The server needs more memory.'",
    "Sastavi tri recenice sa rijecju 'mlijeko'.",
    "Koji padez je upotrijebljen u recenici 'Vidim kucu'?",
    "Napisi kratko uputstvo za kuhanje kafe na bosanskom jeziku.",
]

tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
base = AutoModelForCausalLM.from_pretrained(
    BASE, dtype=torch.bfloat16, device_map="auto", trust_remote_code=True)
model = PeftModel.from_pretrained(base, ADAPTER)
model.eval()


def gen(prompt, max_new=200):
    text_in = tok.apply_chat_template(
        [{"role": "system", "content": SYSTEM},
         {"role": "user", "content": prompt}],
        tokenize=False, add_generation_prompt=True)
    inp = tok([text_in], return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=max_new, temperature=0.0,
                             do_sample=False, pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][inp.input_ids.shape[1]:], skip_special_tokens=True)


fmt_ok = 0
for p in FORMAT_PROMPTS:
    t = gen(p)
    _, _, st = parse_call(t)
    ok = st == "ok"
    fmt_ok += ok
    print(f"{'OK ' if ok else 'FAIL'} [{st}] :: {t[:110]!r}", flush=True)

print("--- ASK (info) ---", flush=True)
for p in ASK_PROMPTS:
    t = gen(p, 150)
    _, _, st = parse_call(t)
    print(f"ASK [{st}] :: {t[:110]!r}", flush=True)

print("--- BOSNIAN (info) ---", flush=True)
for p in BOSNIAN_PROMPTS:
    t = gen(p, 150)
    print(f"BOS :: {t[:110]!r}", flush=True)

print(f"\nFORMAT SCORE: {fmt_ok}/{len(FORMAT_PROMPTS)}")
json.dump({"format": [fmt_ok, len(FORMAT_PROMPTS)]},
          open(OUT, "w"), ensure_ascii=False)
