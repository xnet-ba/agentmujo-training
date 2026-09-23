#!/usr/bin/env python3
"""Audit kontradikcija: isti/normalizovani user prompt -> razlicito ponasanje.
Ponasanje = (ima_tool_block, ima_pitanje_potvrde, je_odbijanje).
Prijavljuje grupe sa >1 razlicitim ponasanjem.
"""
import json
import re
from pathlib import Path
from collections import defaultdict

R = Path("/home/ubuntu/agentmujo-training/datasets/canonical")
FILES = ["function_calling_v0.1.jsonl", "agentic_terminal_v0.1.jsonl",
         "bosnian_core_v0.1.jsonl", "thinking_v0.1.jsonl"]

REF_WORDS = ("ne mogu", "odbijam", "nije dozvoljeno", "ne smijem", "zabranjen")
ASK_WORDS = ("potvrd", "potvrđ", "siguran", "saglas")

def norm(t):
    t = t.lower().strip().rstrip(".!?")
    t = re.sub(r"\s+", " ", t)
    return t

def behavior(m):
    asist = " ".join(x.get("content", "") for x in m if x.get("role") == "assistant").lower()
    has_block = "<function=" in asist or any(
        tc for x in m if x.get("role") == "assistant" for tc in (x.get("tool_calls") or []))
    asks = any(w in asist for w in ASK_WORDS)
    refuses = any(w in asist for w in REF_WORDS)
    if refuses:
        return "REFUSE"
    if has_block and asks:
        return "CALL+ASK"
    if has_block:
        return "CALL"
    if asks:
        return "ASK"
    return "TEXT"

groups = defaultdict(list)
for f in FILES:
    for l in (R / f).read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        users = [m.get("content", "") for m in r["messages"] if m.get("role") == "user"]
        if not users:
            continue
        groups[norm(users[0])].append((r["id"], behavior(r["messages"])))

n_contra = 0
for prompt, items in sorted(groups.items()):
    behs = {b for _, b in items}
    if len(behs) > 1 and len(items) > 1:
        n_contra += 1
        print(f"CONTRADICT [{len(items)}x]: {prompt[:80]!r}")
        for i, b in items:
            print(f"    {i}: {b}")
print(f"\nUkupno tacnih duplikat-prompts: {sum(1 for v in groups.values() if len(v)>1)}, od toga kontradiktornih: {n_contra}")
