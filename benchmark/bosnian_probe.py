#!/usr/bin/env python3
"""Bosanska proba baze — odluka treba li bosnian-core skup.

12 promptova sa zamkama za ekavizme i generativni kvalitet (Q8, read-only).
Automatska heuristika + sacuvani izvadci za ljudsku ocjenu.
Rezultat: benchmark/results_bosnian_probe.json + docs/BOSNIAN_PROBE.md
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.benchmark.runner import EKAVIAN_MARKERS  # noqa: E402

SYSTEM = ("Ti si koristan asistent. Odgovaraj uvijek na bosanskom jeziku "
          "(ijekavica). Budi precizan, jasan i koristan.")

PROMPTS = [
    ("bp-01", "znanje", "Objasni ukratko šta je fotosinteza."),
    ("bp-02", "generacija", "Napiši kratku čestitku za rođendan na bosanskom jeziku."),
    ("bp-03", "rječnik", "Koja je razlika između riječi 'vrijeme' i 'vrijednost'?"),
    ("bp-04", "prevod", "Prevedi na bosanski jezik: 'The server needs more memory.'"),
    ("bp-05", "registar", "Objasni djetetu šta je internet."),
    ("bp-06", "ijekavica-zamka", "Sastavi tri rečenice sa riječju 'mlijeko'."),
    ("bp-07", "rječnik", "Šta znači riječ 'džep'?"),
    ("bp-08", "ijekavica-zamka", "Napiši kratku vijest o vremenskoj prognozi za Sarajevo."),
    ("bp-09", "gramatika", "Objasni razliku između 'da li' i 'je li' u bosanskom jeziku."),
    ("bp-10", "sažimanje", "Sažmi u dvije rečenice: 'Linux je porodica operativnih sistema otvorenog koda koju je započeo Linus Torvalds. Danas pokreće većinu servera, superračunara i Android telefona.'"),
    ("bp-11", "gramatika", "Koji padež je upotrijebljen u rečenici 'Vidim kuću'?"),
    ("bp-12", "ijekavica-zamka", "Napiši kratko uputstvo za kuhanje kafe na bosanskom jeziku."),
]


def query(prompt: str, timeout: int = 300, model: str = "qwen3.5-2b-bos-q8:latest") -> tuple[str, float]:
    t0 = time.time()
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps({
            "model": model,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": prompt}],
            "think": False, "stream": False,
            "options": {"temperature": 0.7, "num_predict": 300},
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    return d.get("message", {}).get("content", ""), time.time() - t0


def auto_score(text: str) -> dict:
    lowered = (text or "").lower()
    hits = [w for w in EKAVIAN_MARKERS if w in lowered]
    return {
        "non_empty": 1 if text.strip() else 0,
        "no_ekavian": 0 if hits else 1,
        "ekavian_hits": hits,
        "length_chars": len(text),
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3.5-2b-bos-q8:latest")
    ap.add_argument("--out", default=str(REPO / "benchmark" / "results_bosnian_probe.json"))
    a = ap.parse_args()
    out_path = Path(a.out)
    results = []
    for pid, cat, prompt in PROMPTS:
        try:
            text, lat = query(prompt, model=a.model)
            scores = auto_score(text)
            err = None
        except Exception as e:
            text, lat, scores, err = "", None, {}, f"{type(e).__name__}: {e}"
        results.append({"id": pid, "category": cat, "prompt": prompt,
                        "text": text, "latency_s": round(lat, 1) if lat else None,
                        "auto": scores, "error": err})
        print(f"[{pid}] ekavian={scores.get('ekavian_hits', '?')} "
              f"len={scores.get('length_chars', 0)} ({lat:.1f}s)" if lat else f"[{pid}] GREŠKA",
              flush=True)
    ok = [r for r in results if not r["error"]]
    summary = {
        "n": len(ok),
        "non_empty_rate": round(sum(r["auto"]["non_empty"] for r in ok) / len(ok), 3),
        "no_ekavian_rate": round(sum(r["auto"]["no_ekavian"] for r in ok) / len(ok), 3),
    }
    out_path.write_text(json.dumps({"summary": summary, "results": results},
                                   indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
