#!/usr/bin/env python3
"""Format-proba THINK rezim, produkcijski SYSTEM. Prvih N slucajeva.
Upotreba: python benchmark/format_probe_think.py <model> [N=10]
"""
from __future__ import annotations
import sys
sys.path.insert(0, "benchmark")
from two_step_eval import chat, parse  # noqa: E402
from format_probe_prod import PROD_SYSTEM  # noqa: E402
sys.path.insert(0, "src")
from agentmujo_training.benchmark import load_cases  # noqa: E402

def main() -> int:
    model = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    cases = [c for c in load_cases("benchmark/cases_v0.5.jsonl")][:n]
    ok = 0
    for c in cases:
        base = [{"role": "system", "content": PROD_SYSTEM},
                {"role": "user", "content": c.prompt}]
        try:
            text = chat(model, base, True, 512)
        except Exception as e:
            print(f"ERR {c.id}: {e}", flush=True)
            continue
        tool, args = parse(text)
        mark = "OK " if tool else "FAIL"
        if tool:
            ok += 1
        print(f"{mark} {c.id} tool={tool} args={args} :: {text[:150]!r}", flush=True)
    print(f"\nTHINK FORMAT SCORE: {ok}/{len(cases)} = {ok/len(cases):.2f}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
