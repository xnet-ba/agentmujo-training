#!/usr/bin/env python3
"""Build datasets/canonical/joint_train_v0.42.jsonl — 9B-joint-09 HL-fix SFT.

Lekcija joint08 (tool 0.867, safety 0.714, ALI high_level 1.0->0.6):
HL bench slucajevi eksplicitno traze "kroz terminal", a metrika nagradjuje
high-level alat UPRKOS tome. Safety demonstracije su pojacale doslovnu
poslusnost -> model slusa "terminal" i gubi HL poene.
Antidot: redovi gdje korisnik trazi terminal a asistent odgovara
high-level alatom (override pattern, gold03 lekcija). Nadjeno 42 takva
reda u FC/AG kanonu — idu SVI u mix + HL-first filter na ostalo.
Sastav ~1900: FC hard/med HL-first 700 + AG hard/med HL-first 400 +
safety SFT 300 + confirmation ask-first 200 + BC plain 200 +
override terminal->HL 42 + think 50. Baza: joint08 adapter.
Seed 42. Deterministicki. Ne dira postojece fajlove ni splits/.
"""
import json
import random
from pathlib import Path

RNG = random.Random(42)
ROOT = Path(__file__).resolve().parent.parent
CAN = ROOT / "datasets" / "canonical"
OUT = CAN / "joint_train_v0.42.jsonl"

FC_FILES = [f"function_calling_v0.{v}.jsonl" for v in ("2", "3", "4", "5")]
AG_FILES = [f"agentic_terminal_v0.{v}.jsonl" for v in ("1", "2", "3", "4", "5")]
BC_FILES = ["bosnian_core_v0.2.jsonl", "bosnian_core_v0.3.jsonl"]
SF_FILES = [f"safety_v0.{v}.jsonl" for v in ("3", "4", "5")]
CF_FILES = [f"confirmation_v0.{v}.jsonl" for v in ("1", "2", "3", "4")]


def load(files):
    rows = []
    for f in files:
        p = CAN / f
        if p.exists():
            rows += [json.loads(l) for l in open(p) if l.strip()]
    return rows


def ok_msg(r):
    ms = r.get("messages")
    return bool(ms) and isinstance(ms, list) and len(ms) >= 2


def first_tool(row):
    for m in row.get("messages", []):
        tcs = m.get("tool_calls") or []
        if tcs:
            return tcs[0].get("name")
    return None


def mentions_terminal(row):
    ms = row.get("messages", [])
    first_user = next((m.get("content", "") for m in ms if m.get("role") == "user"), "")
    t = first_user.lower()
    return "terminal" in t or "kroz komand" in t or "komandom" in t


def pick(rows, n, seen):
    rows = [r for r in rows if ok_msg(r) and r["id"] not in seen]
    RNG.shuffle(rows)
    out = rows[:n]
    seen.update(r["id"] for r in out)
    return out


seen = set()
fc = [r for r in load(FC_FILES) if r.get("difficulty") in ("hard", "medium")]
fc = [r for r in fc if first_tool(r) not in (None, "terminal")]
ag = load(AG_FILES)
ag_hard = [r for r in ag if r.get("difficulty") == "hard"
           and first_tool(r) not in (None, "terminal")]
ag_med = [r for r in ag if r.get("difficulty") == "medium"
          and first_tool(r) not in (None, "terminal")]
# Override: korisnik trazi terminal, asistent otvara high-level alatom.
override_pool = [r for r in load(FC_FILES + ["function_calling_v0.1.jsonl"]) + ag
                 if mentions_terminal(r) and first_tool(r) not in (None, "terminal")]
sf = load(SF_FILES)
cf = [r for r in load(CF_FILES) if first_tool(r) is None]
bc = [r for r in load(BC_FILES) if first_tool(r) is None]
think = [r for r in ag if r.get("enable_thinking")]

ov = pick(override_pool, len(override_pool), seen)
sel = (pick(fc, 700, seen) + pick(ag_hard, 280, seen)
       + pick(ag_med, 120, seen) + pick(sf, 300, seen)
       + pick(cf, 200, seen) + pick(bc, 200, seen)
       + pick(think, 50, seen) + ov)
ids = [r["id"] for r in sel]
assert len(ids) == len(set(ids)), "duplikati u mixu!"
RNG.shuffle(sel)
OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in sel) + "\n")
n_tool = sum(1 for r in sel if first_tool(r))
print(f"joint-09-9b: {len(sel)} (tool {n_tool}, override {len(ov)})")
