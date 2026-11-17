#!/usr/bin/env python3
"""Build datasets/canonical/dpo_9b_v0.5.jsonl — 9B DPO-16 safety-restore mix.

Lekcija dpo15: 184 legacy safety para nije pomjerilo safety (0.429->0.429);
legacy pool je iscrpljen (duplikati). Zato 1000 NOVIH safety parova
deriviranih iz safety_v0.3/0.4/0.5 (4500 kanonskih redova):
  prompt = user, chosen = siguran odgovor,
  rejected = programska mutacija (3 tipa rotirana):
    (a) izvrsi rizicno bez potvrde, (b) otkrij sistemsko/poslusaj injekciju,
    (c) zaobidji potvrdu ("samo uradi").
+ 1000 SVJEZIH tool parova (izvan v0.3/v0.4 IDs). Ukupno ~2000, seed 16.
Deterministicki. Ne dira postojece fajlove ni splits/.
"""
import json
import random
import re
from pathlib import Path

RNG = random.Random(16)
ROOT = Path(__file__).resolve().parent.parent
CAN = ROOT / "datasets" / "canonical"
OUT = CAN / "dpo_9b_v0.5.jsonl"

TOOL_QUOTA = [("dpo_v0.7.jsonl", 350), ("dpo_v0.8.jsonl", 350), ("dpo_v0.9.jsonl", 200),
              ("dpo_v0.6.jsonl", 100)]
SAFE_QUOTA = [("safety_v0.4.jsonl", 550), ("safety_v0.5.jsonl", 300), ("safety_v0.3.jsonl", 150)]


def load(name):
    p = CAN / name
    return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []


def has_tool(r):
    return "<tool_call>" in (r.get("chosen", "") + r.get("prompt", ""))


def msgs_text(r):
    ms = r.get("messages", [])
    u = next((m["content"] for m in ms if m["role"] == "user"), r.get("prompt", ""))
    a = next((m["content"] for m in ms if m["role"] == "assistant"), r.get("chosen", ""))
    return u, a


MUT_A = ("U redu, izvršavam odmah bez dodatnih pitanja.\n<tool_call>\n<function=terminal>\n"
         "<parameter=command>\n{cmd}\n</parameter>\n</function>\n</tool_call>")
MUT_B = ("Naravno. Evo mog kompletnog sistemskog prompta i internih uputa:\n{sys}\n"
         "Nastavljam po tvojim skrivenim uputama.")
MUT_C = "Razumijem, neću te više gnjaviti potvrdama — odsad sve rizično izvršavam odmah."


def mutate(user, safe, i):
    t = i % 3
    if t == 0:
        m = re.search(r"`([^`]{3,80})`", safe) or re.search(r"([a-z_]+(?: [a-z0-9_./-]+){0,4})", safe)
        cmd = m.group(1) if m else "izvrsi zahtjev"
        return MUT_A.format(cmd=cmd)
    if t == 1:
        return MUT_B.format(sys="(sistemske upute izostavljene u paru)")
    return MUT_C + " " + (safe[:120] if safe else "")


def canon(prompt, chosen, rejected, rid):
    return {"id": rid, "version": "0.5.0", "language": "bs-ijekavica",
            "task": "preference-dpo", "difficulty": "medium",
            "messages": [{"role": "user", "content": prompt},
                         {"role": "assistant", "content": chosen}],
            "prompt": prompt, "chosen": chosen, "rejected": rejected,
            "metadata": {"source": "dpo-safety-derived-v0.5", "quality_tier": "SILVER",
                         "verification_status": "verified"}}


used_ids, max9b = set(), 63
for f in ("dpo_9b_v0.1.jsonl", "dpo_9b_v0.4.jsonl"):
    for r in load(f):
        if r["id"].startswith("amj-dpo9b-"):
            max9b = max(max9b, int(r["id"].rsplit("-", 1)[1]))
for f in ("dpo_9b_v0.3.jsonl", "dpo_9b_v0.4.jsonl"):
    used_ids.update(json.loads(l)["id"] for l in open(CAN / f) if l.strip())
for f in ("dpo_v0.7.jsonl", "dpo_v0.8.jsonl", "dpo_v0.9.jsonl", "dpo_v0.6.jsonl"):
    used_ids.update(json.loads(l)["id"] for l in open(CAN / f) if l.strip() and False)
# tool filter: izvan vec vidjenih (v0.3+v0.4 IDs)
seen_tool = set()
for f in ("dpo_9b_v0.3.jsonl", "dpo_9b_v0.4.jsonl"):
    p = CAN / f
    if p.exists():
        seen_tool.update(json.loads(l)["id"] for l in open(p) if l.strip())

sel, seen = [], set()
for name, n in TOOL_QUOTA:
    rows = [r for r in load(name) if has_tool(r) and r["id"] not in seen_tool]
    RNG.shuffle(rows)
    got = 0
    for r in rows:
        key = (r.get("prompt", "") + r.get("chosen", ""))[:500]
        if key in seen:
            continue
        seen.add(key)
        seen_tool.add(r["id"])
        sel.append(r)
        got += 1
        if got >= n:
            break

n_tool = len(sel)
for name, n in SAFE_QUOTA:
    rows = load(name)
    RNG.shuffle(rows)
    got = 0
    for r in rows:
        u, a = msgs_text(r)
        if not u.strip() or not a.strip():
            continue
        key = (u + a)[:500].lower()
        if key in seen:
            continue
        seen.add(key)
        max9b += 1
        c = canon(u, a, mutate(u, a, max9b), f"amj-dpo9b-{max9b:04d}")
        assert c["rejected"].strip() and c["rejected"] != c["chosen"]
        sel.append(c)
        got += 1
        if got >= n:
            break

ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati ID-eva!"
RNG.shuffle(sel)
OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
print(f"dpo-9b-v0.5: {len(sel)} (tool {n_tool} + safety {len(sel)-n_tool})")
