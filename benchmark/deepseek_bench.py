#!/usr/bin/env python3
"""AgentMujo-Bench protiv vanjskog OpenAI-kompatibilnog modela (npr. DeepSeek).

Ista metrika kao llama_bench (isti scorer, isti produkcijski SYSTEM),
samo transport s Bearer kljucem + model parametar.
Ne izlaze API kljucevi: kljuc ide iz env varijable, nikad u repo.

Upotreba (DeepSeek API):
  export DEEPSEEK_API_KEY=sk-...
  python benchmark/deepseek_bench.py deepseek-chat nonthink \
      benchmark/cases_v0.5.jsonl benchmark/results_deepseek_v41_flash_nonthink.json
  Modeli: deepseek-chat (V4.x chat) ili deepseek-reasoner (think mod).
  Custom endpoint: DEEPSEEK_BASE_URL (default https://api.deepseek.com).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "benchmark"))

from agentmujo_training.benchmark import load_cases, score_prediction  # noqa: E402
from two_step_eval import FUNC_RE  # noqa: E402
import llama_bench  # noqa: E402  (dijeli parse(); SYSTEM preuzet odatle)
from llama_bench import parse, SYSTEM  # noqa: E402

BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")


def chat(model: str, key: str, messages: list[dict], max_tokens: int, timeout: int = 600) -> str:
    body = {"model": model, "messages": messages, "stream": False,
            "temperature": 0.0, "max_tokens": max_tokens}
    req = urllib.request.Request(
        BASE_URL + "/v1/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    msg = d["choices"][0]["message"]
    # reasoning modeli: reasoning_content + content
    return (msg.get("content") or "") + ("" if not msg.get("reasoning_content") else "")


def main() -> int:
    model, mode, cases_path, out_path = sys.argv[1:5]
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        print("GRESKA: postavi DEEPSEEK_API_KEY env varijablu (nikad u repo).", file=sys.stderr)
        return 2
    think = mode == "think"
    results = []
    for c in load_cases(cases_path):
        t0 = time.time()
        try:
            base = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": c.prompt}]
            text = chat(model, key, base, 1024 if think else 512)
            tool, args = parse(text)
            scores = score_prediction(c, tool, args, text)
            results.append({"case": c.id, "tool": tool, "args": args,
                            "scores": scores, "trace": [tool],
                            "lat": round(time.time() - t0, 1), "text": (text or "")[:800]})
        except Exception as e:
            results.append({"case": c.id, "tools": [], "scores": {}, "error": str(e)[:200]})
        print(f"[{c.id}] {results[-1].get('tool')} {results[-1].get('scores')}", flush=True)
    agg: dict[str, list] = {}
    for r in results:
        for k, v in r.get("scores", {}).items():
            agg.setdefault(k, []).append(v)
    summary = {k: {"n": len(v), "mean": round(sum(v) / len(v), 3)} for k, v in sorted(agg.items())}
    Path(out_path).write_text(json.dumps(
        {"profile": f"deepseek-{model}-{mode}", "summary": summary, "results": results},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
