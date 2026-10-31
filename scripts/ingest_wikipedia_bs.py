#!/usr/bin/env python3
"""Ingest bs Wikipedia intro extracts -> canonical knowledge JSONL (CC BY-SA, extractive)."""
import json, time, urllib.parse, urllib.request
from pathlib import Path

OUT = Path("datasets/canonical/knowledge_wikipedia_bs_v0.2.jsonl")
API = "https://bs.wikipedia.org/w/api.php"
rows, seen = [], set()
for attempt in range(80):
    q = urllib.parse.urlencode({"action": "query", "generator": "random", "grnnamespace": "0",
        "grnlimit": "10", "prop": "extracts", "explaintext": "1", "exintro": "1",
        "format": "json", "formatversion": "2"})
    try:
        req = urllib.request.Request(API + "?" + q, headers={"User-Agent": "AgentMujoDatasetFactory/0.2 (https://github.com/xnet-ba/agentmujo-training; dataset@agentmujo.ai)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print("api", e); time.sleep(2); continue
    for p in data.get("query", {}).get("pages", []) or []:
        title = str(p.get("title") or "").strip()
        ext = str(p.get("extract") or "").strip()
        if not title or len(ext) < 250 or title in seen:
            continue
        seen.add(title)
        rows.append({
            "id": f"amj-kn-{len(rows)+1:04d}", "version": "0.3.0", "language": "bs",
            "task": "bosnian-knowledge", "difficulty": "easy",
            "messages": [
                {"role": "user", "content": f"Šta piše o temi „{title}“ na bosanskoj Wikipediji?"},
                {"role": "assistant", "content": ext[:900]},
            ],
            "metadata": {"source": "wikipedia-bs", "license": "CC BY-SA 4.0",
                         "url": "https://bs.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")),
                         "verification_status": "source-grounded", "quality_tier": "SILVER",
                         "retrieved_at": time.strftime("%Y-%m-%d")},
        })
        if len(rows) >= 200:
            break
    if len(rows) >= 200:
        break
    time.sleep(0.3)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
print("knowledge rows", len(rows), "->", OUT)
