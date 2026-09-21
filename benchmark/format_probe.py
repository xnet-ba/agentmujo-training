#!/usr/bin/env python3
"""Brza format-proba: prvih N tool_selection slucajeva, samo prvi korak.
Isti SYSTEM prompt i chat() kao two_step_eval.py — mjeri da li model
izbacuje kanonski <function=> format (parse) ili kolapsirani.
Upotreba: python benchmark/format_probe.py <model> [N=10]
"""
from __future__ import annotations
import json
import sys
sys.path.insert(0, "benchmark")
from two_step_eval import SYSTEM, chat, parse  # noqa: E402
sys.path.insert(0, "src")
from agentmujo_training.benchmark import load_cases  # noqa: E402

def main() -> int:
    model = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    cases = [c for c in load_cases("benchmark/cases_v0.5.jsonl")][:n]
    ok = 0
    for c in cases:
        base = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": c.prompt}]
        try:
            text = chat(model, base, False, 256)
        except Exception as e:
            print(f"ERR {c.id}: {e}")
            continue
        tool, args = parse(text)
        mark = "OK " if tool else "FAIL"
        if tool:
            ok += 1
        print(f"{mark} {c.id} tool={tool} args={args} :: {text[:120]!r}")
    print(f"\nFORMAT SCORE: {ok}/{len(cases)} = {ok/len(cases):.2f}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
