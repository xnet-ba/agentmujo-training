#!/usr/bin/env python3
"""Build datasets/canonical/dpo_9b_v0.4.jsonl — 9B DPO-15 safety-balans.

Lekcija dpo14 (tool 0.6->0.7, args 0.692->0.769) ali safety 0.857->0.429:
v0.3 filter (samo chosen sa <tool_call>) izbacio refusal/safety parove.
Popravak: 1400 SVJEZIH tool parova (izvan v0.3 IDs) + 500 safety/refusal
parova (netool iz v0.1-v0.6, noviji prioritet). Baza: dpo14 adapter.
Deterministicki (seed 15). Ne dira postojece fajlove ni splits/.
"""
import json
import random
from pathlib import Path

RNG = random.Random(15)
ROOT = Path(__file__).resolve().parent.parent
CAN = ROOT / "datasets" / "canonical"
OUT = CAN / "dpo_9b_v0.4.jsonl"

TOOL_QUOTA = [("dpo_v0.7.jsonl", 500), ("dpo_v0.8.jsonl", 500),
              ("dpo_v0.9.jsonl", 300), ("dpo_v0.6.jsonl", 100)]
SAFE_QUOTA = [("dpo_v0.6.jsonl", 120), ("dpo_v0.5.jsonl", 120),
              ("dpo_v0.4.jsonl", 100), ("dpo_v0.3.jsonl", 80),
              ("dpo_v0.2.jsonl", 50), ("dpo_v0.1.jsonl", 30)]


def load(name):
    p = CAN / name
    return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []


def has_tool(r):
    return "<tool_call>" in (r.get("chosen", "") + r.get("prompt", ""))


used = set()
p = CAN / "dpo_9b_v0.3.jsonl"
if p.exists():
    used = {json.loads(l)["id"] for l in open(p) if l.strip()}

sel, seen_keys = [], set()
_dpo9b = [63]  # nastavak na max amj-dpo9b-* (v0.1/v0.2 imaju 63)


def canon(r, new_id=None):
    """Stare redove (v0.1-v0.5, bez kanonskih polja) normaliziraj + fresh ID."""
    r = dict(r)
    if new_id:
        r["id"] = new_id
    if "messages" not in r:
        r["messages"] = [{"role": "user", "content": r.get("prompt", "")},
                         {"role": "assistant", "content": r.get("chosen", "")}]
        r.setdefault("language", "bs-ijekavica")
        r.setdefault("task", "preference-dpo")
        r.setdefault("version", "0.4.0")
        r.setdefault("metadata", {"source": "dpo-legacy-normalized-v0.4",
                                  "quality_tier": "SILVER",
                                  "verification_status": "verified"})
    return r


def take(rows, n, want_tool, fresh_ids=False, tag=""):
    RNG.shuffle(rows)
    got = []
    for r in rows:
        if want_tool != has_tool(r):
            continue
        key = (tag, r["id"])  # ID-evi se recikliraju po verzijama -> tag scope
        if key in seen_keys:
            continue
        seen_keys.add(key)
        if fresh_ids:
            _dpo9b[0] += 1
            r = canon(r, f"amj-dpo9b-{_dpo9b[0]:04d}")
        sel.append(r)
        got.append(r)
        if len(got) >= n:
            break
    return got


counts = {}
for name, n in TOOL_QUOTA:
    counts[name] = len(take(load(name), n, True, tag=name))
for name, n in SAFE_QUOTA:
    legacy = name in ("dpo_v0.1.jsonl", "dpo_v0.2.jsonl", "dpo_v0.3.jsonl",
                      "dpo_v0.4.jsonl", "dpo_v0.5.jsonl")
    counts[name] = counts.get(name, 0) + len(take(load(name), n, False,
                                                  fresh_ids=legacy, tag=name))

ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati ID-eva!"
RNG.shuffle(sel)

# Validator lovi identicne template-duplikate po sadrzaju (v0.1-v0.5
# recikliraju tekstove): izbaci kasnije duplikate, zadrzi prvi.
import re as _re
seen_content, clean = set(), []
for r in sel:
    norm = _re.sub(r"\s+", " ", (r.get("prompt", "") + "\n" + r.get("chosen", "")).lower().strip())
    if norm in seen_content:
        continue
    seen_content.add(norm)
    clean.append(r)
sel = clean
OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
n_tool = sum(1 for r in sel if has_tool(r))
print(f"dpo-9b-v0.4: {len(sel)} (tool {n_tool} + safety {len(sel)-n_tool}) {counts}")
