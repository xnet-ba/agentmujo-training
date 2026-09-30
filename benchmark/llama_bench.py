#!/usr/bin/env python3
"""Bench kroz llama-server (OpenAI endpoint) umjesto Ollame.
Ista metrika kao two_step_eval (isti scorer, isti produkcijski SYSTEM),
samo transport drugaciji — za modele koji ne staju u Ollama import.

Upotreba: python benchmark/llama_bench.py <endpoint> <think|nonthink> <cases> <out>
  endpoint npr. http://127.0.0.1:8080
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "benchmark"))

from agentmujo_training.benchmark import load_cases, score_prediction  # noqa: E402
import two_step_eval  # noqa: E402
from two_step_eval import FUNC_RE, INT_ARGS  # noqa: E402
import bench_prod  # noqa: E402  (postavlja produkcijski SYSTEM na two_step_eval.SYSTEM)
SYSTEM = two_step_eval.SYSTEM


def chat(endpoint: str, messages: list[dict], max_tokens: int, timeout: int = 600) -> str:
    body = {"messages": messages, "stream": False,
            "temperature": 0.0, "max_tokens": max_tokens}
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    return d["choices"][0]["message"]["content"]


def parse(text: str):
    m = FUNC_RE.search(text or "")
    if not m:
        return None, None
    args: dict = {}
    import re as _re
    for k, v in _re.findall(r"<parameter=([a-z_][a-z0-9_]*)>(.*?)</parameter>", text, _re.IGNORECASE | _re.DOTALL):
        v = v.strip()
        args[k] = int(v) if k in INT_ARGS and v.isdigit() else v
    return m.group(1), args


def main() -> int:
    endpoint, mode, cases_path, out_path = sys.argv[1:5]
    think = mode == "think"
    results = []
    for c in load_cases(cases_path):
        t0 = time.time()
        try:
            base = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": c.prompt}]
            text = chat(endpoint, base, 512 if think else 256)
            tool, args = parse(text)
            scores = score_prediction(c, tool, args, text)
            trace = [tool]
            if c.must_verify and tool is not None:
                follow = (base + [{"role": "assistant", "content": text}]
                          + [{"role": "user", "content": "<tool_response>\n{'result': 'ok'}\n</tool_response>"}])
                text2 = chat(endpoint, follow, 128)
                m2 = FUNC_RE.search(text2 or "")
                tool2 = m2.group(1) if m2 else None
                trace.append(tool2)
                if tool2 is not None:
                    scores["multi_step"] = 1 if c.expected_tool in trace else 0
                    if tool2 == c.expected_tool:
                        scores["tool_selection"] = 1
            results.append({"case": c.id, "tool": tool, "args": args,
                            "scores": scores, "trace": trace,
                            "lat": round(time.time() - t0, 1), "text": (text or "")[:800]})
        except Exception as e:
            results.append({"case": c.id, "tools": [], "scores": {}, "error": str(e)[:100]})
        print(f"[{c.id}] {results[-1].get('tool')} {results[-1].get('scores')}", flush=True)
        Path(out_path).write_text(json.dumps(
            {"profile": f"llama-server-{mode}", "partial": True, "results": results},
            indent=2, ensure_ascii=False), encoding="utf-8")
    agg: dict[str, list] = {}
    for r in results:
        for k, v in r.get("scores", {}).items():
            agg.setdefault(k, []).append(v)
    summary = {k: {"n": len(v), "mean": round(sum(v) / len(v), 3)} for k, v in sorted(agg.items())}
    Path(out_path).write_text(json.dumps(
        {"profile": f"llama-server-{mode}", "summary": summary, "results": results},
        indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
