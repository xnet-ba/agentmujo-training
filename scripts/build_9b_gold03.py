#!/usr/bin/env python3
"""9B-gold03 subset: high-level-first dijalekt + ask-first + plain.
Lekcija iz gold02 gatea: check-then-ask je ZELJENO ponasanje (scorer ga
kaznjava, ali je sigurnije od slijepog pitanja) — ne trenirati protiv
njega. Pravi gap je high_level (terminal fallback): zato prednost
redovima ciji je PRVI tool_call high-level alat, ne terminal.
Sastav (~4.2k): AG hard HL + AG med HL 400 + FC hard HL + verification/
tool-selection/reasoning hard + 600 confirmation ask-first (500 no-tool
+ 100 with-tool, hard) + 400 BC plain (no tool_calls, easy).
Deterministicki (seed 37). Izlaz: jsonl.
Upotreba: python scripts/build_9b_gold03.py <joint_train.jsonl> <izlaz.jsonl>
"""
import json
import random
import sys

CONF_FILES = [
    "datasets/canonical/confirmation_v0.2.jsonl",
    "datasets/canonical/confirmation_v0.3.jsonl",
    "datasets/canonical/confirmation_v0.4.jsonl",
]


def first_tool(row):
    for m in row.get("messages", []):
        tcs = m.get("tool_calls") or []
        if tcs:
            return tcs[0].get("name")
    return None


def main(inp, outp):
    rng = random.Random(37)
    rows = [json.loads(l) for l in open(inp)]

    conf = []
    for f in CONF_FILES:
        conf += [json.loads(l) for l in open(f)]
    ask = [r for r in conf if r.get("difficulty") == "hard"
           and not any(m.get("tool_calls") for m in r["messages"])]
    act = [r for r in conf if r.get("difficulty") == "hard"
           and any(m.get("tool_calls") for m in r["messages"])]
    rng.shuffle(ask)
    rng.shuffle(act)
    keep_conf = ask[:500] + act[:100]
    cids = set(r["id"] for r in keep_conf)

    def pool(task, diff):
        pl = [r for r in rows if r.get("task") == task
              and (diff is None or r.get("difficulty") == diff)
              and r["id"] not in cids
              and first_tool(r) not in (None, "terminal")]
        rng.shuffle(pl)
        return pl

    sel = (pool("agentic-terminal", "hard") + pool("agentic-terminal", "medium")[:400]
           + pool("function-calling", "hard") + pool("verification", None)
           + pool("tool-selection", None) + pool("reasoning", "hard")
           + keep_conf)

    plain = [r for r in rows if r.get("task") == "bosnian-core"
             and r.get("difficulty") == "easy"
             and not any(m.get("tool_calls") for m in r["messages"])
             and r["id"] not in cids]
    rng.shuffle(plain)
    sel += plain[:400]

    ids = [r["id"] for r in sel]
    assert len(ids) == len(set(ids)), "DUPLIKATI!"
    rng.shuffle(sel)
    with open(outp, "w") as f:
        for r in sel:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"gold03: {len(sel)} rows -> {outp}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
