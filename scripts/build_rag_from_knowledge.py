#!/usr/bin/env python3
"""Build RAG samples from the Wikipedia knowledge set (extractive, source-grounded)."""
import json
from pathlib import Path

src = Path("datasets/canonical/knowledge_wikipedia_bs_v0.2.jsonl")
out = Path("datasets/canonical/rag_wikipedia_bs_v0.2.jsonl")
rows = []
for line in src.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    k = json.loads(line)
    q = k["messages"][0]["content"]
    ctx = k["messages"][1]["content"]
    rows.append({
        "id": f"amj-rg-{len(rows)+1:04d}", "version": "0.3.0", "language": "bs",
        "task": "rag-memory", "difficulty": "medium",
        "messages": [
            {"role": "user", "content": f"Kontekst:\n{ctx}\n\nPitanje: {q}"},
            {"role": "assistant", "content": ctx},
        ],
        "metadata": {"source": "wikipedia-bs", "license": "CC BY-SA 4.0",
                     "verification_status": "source-grounded", "synthetic": True,
                     "quality_tier": "SILVER", "derived_from": k["id"]},
    })
    if len(rows) >= 100:
        break
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
print("rag rows", len(rows), "->", out)
