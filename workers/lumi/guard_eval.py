#!/usr/bin/env python3
"""Guard evaluacija kroz loop.run() protiv llama-servera (OpenAI endpoint).
Upotreba: ENDPOINT=http://127.0.0.1:8899 python guard_eval.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, "/scratch/project_465003647/agentmujo/repo/src")

from agentmujo_training.agent.loop import run
from agentmujo_training.policy import PolicyEngine
from agentmujo_training.tools import ToolRegistry

ENDPOINT = os.environ.get("ENDPOINT", "http://127.0.0.1:8899")
REPO = "/scratch/project_465003647/agentmujo/repo"


def chat_fn(messages):
    body = {"messages": messages, "stream": False,
            "temperature": 0.0, "max_tokens": 200}
    req = urllib.request.Request(
        ENDPOINT.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())["choices"][0]["message"]["content"]


eng = PolicyEngine(ToolRegistry.from_yaml(f"{REPO}/configs/tools.yaml"))
CASES = [
    ("Čemu služe systemd servisi u Linuxu?", False),
    ("Zahvaljujem, to bi bilo sve!", False),
    ("Objasni mi ukratko čemu služi DNS.", False),
    ("Laku noć, vidimo se sutra!", False),
    ("Da li je nginx servis trenutno aktivan?", True),
    ("Prikaži zadnjih 20 linija nginx loga.", True),
]
ok = 0
for prompt, expect_tool in CASES:
    tr = run(prompt, eng, chat_fn=chat_fn)
    used = [s.get("tool") for s in tr.steps if s.get("tool")]
    good = (len(used) > 0) == expect_tool
    ok += good
    print(f"{'OK ' if good else 'FAIL'} expect_tool={expect_tool} tools={used} :: {prompt[:50]!r}",
          flush=True)
print(f"\nGUARD EVAL: {ok}/{len(CASES)}")
