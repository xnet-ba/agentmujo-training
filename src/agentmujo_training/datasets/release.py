"""AgentMujo Dataset Release v0.1: složi verzionirani release iz kanonskih fajlova."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .factory import build_dataset, read_jsonl, write_jsonl, distribution
from .validator import sample_hash

ALL_CATEGORIES = [
    "bosnian-language", "instructions", "knowledge", "function-calling", "tool-use-mcp",
    "agentic-tasks", "linux-terminal", "coding", "reasoning", "rag-memory",
    "safety", "preference-dpo", "agentic-evaluation",
]
MESSAGE_SPECS = [
    {"name": "agentmujo-bosnian-language", "file": "bosnian_core_v0.1.jsonl",
     "categories": ["bosnian-language", "instructions"]},
    {"name": "agentmujo-function-calling", "file": "function_calling_v0.1.jsonl",
     "categories": ["function-calling", "tool-use-mcp"]},
    {"name": "agentmujo-agentic-tasks", "file": "agentic_terminal_v0.1.jsonl",
     "categories": ["agentic-tasks", "linux-terminal"]},
    {"name": "agentmujo-reasoning", "file": "thinking_v0.1.jsonl",
     "categories": ["reasoning"]},
    {"name": "agentmujo-safety", "file": "confirmation_v0.1.jsonl",
     "categories": ["safety"]},
]
PREFERENCE_SPEC = {"name": "agentmujo-preference-dpo", "file": "dpo_v0.5.jsonl",
                   "categories": ["preference-dpo"]}


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _preference(repo: Path, spec: dict[str, Any], out: Path, version: str) -> dict[str, Any]:
    src = repo / "datasets" / "canonical" / spec["file"]
    rows = read_jsonl(src)
    d = out / spec["name"]
    d.mkdir(parents=True, exist_ok=True)
    data = d / "data.jsonl"
    write_jsonl(data, rows)
    langs = distribution(rows, "language")
    man = {"schema": "agentmujo.preference.v0", "name": spec["name"], "version": version,
           "created_at": datetime.now(timezone.utc).isoformat(), "source": "own",
           "license": "internal", "data": str(data), "data_sha256": _sha(data),
           "counts": {"input": len(rows), "kept": len(rows), "rejected": 0,
                      "duplicates": 0, "rows": len(rows)},
           "languages": langs or {"?": len(rows)},
           "tasks": {"preference-dpo": len(rows)},
           "format": "prompt/chosen/rejected"}
    (d / "manifest.json").write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"name": spec["name"], "categories": spec["categories"], "rows": len(rows),
            "sha256": man["data_sha256"], "manifest": str(d / "manifest.json"),
            "counts": man["counts"], "languages": man["languages"], "tasks": man["tasks"],
            "format": "preference"}


def build_release(repo: str | Path, version: str = "0.1.0", out_dir: str | Path | None = None) -> dict[str, Any]:
    repo = Path(repo)
    out = Path(out_dir) if out_dir else repo / "releases" / version
    out.mkdir(parents=True, exist_ok=True)
    datasets: list[dict[str, Any]] = []
    covered: set[str] = set()
    errors: list[str] = []
    for spec in MESSAGE_SPECS:
        src = repo / "datasets" / "canonical" / spec["file"]
        if not src.exists():
            errors.append(f"{spec['name']}: nema {src}")
            continue
        try:
            r = build_dataset(src, out / spec["name"], spec["name"], version, source_id="own")
            man = json.loads((out / spec["name"] / "manifest.json").read_text(encoding="utf-8"))
            datasets.append({"name": spec["name"], "categories": spec["categories"],
                             "rows": man["counts"]["rows"], "sha256": man["data_sha256"],
                             "manifest": str(out / spec["name"] / "manifest.json"),
                             "counts": man["counts"], "languages": man.get("languages", {}),
                             "tasks": man.get("tasks", {})})
            covered.update(spec["categories"])
        except Exception as e:
            errors.append(f"{spec['name']}: {e}")
    src = repo / "datasets" / "canonical" / PREFERENCE_SPEC["file"]
    if src.exists():
        try:
            datasets.append(_preference(repo, PREFERENCE_SPEC, out, version))
            covered.update(PREFERENCE_SPEC["categories"])
        except Exception as e:
            errors.append(f"{PREFERENCE_SPEC['name']}: {e}")
    else:
        errors.append(f"{PREFERENCE_SPEC['name']}: nema {src}")
    gaps = [c for c in ALL_CATEGORIES if c not in covered]
    total = sum(int(d.get("rows") or 0) for d in datasets)
    release = {
        "schema": "agentmujo.release.v0", "name": "AgentMujo Dataset", "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(), "repository": str(repo),
        "datasets": datasets, "covered_categories": sorted(covered), "gaps": gaps,
        "total_rows": total, "gpu_used": False, "lumi_used": False,
        "notes": "v0.1.0 je reprezentativni release iz postojećih kanonskih fajlova; "
                 "gapovi su stvarni, nisu popunjeni izmišljenim podacima. Agentic-evaluation je odvojen benchmark.",
        "errors": errors,
    }
    (out / "RELEASE.json").write_text(json.dumps(release, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [f"# AgentMujo Dataset Card — v{version}", "", f"**Ukupno redova:** {total}",
             f"**Kategorije:** {', '.join(sorted(covered))}", f"**Gapovi:** {', '.join(gaps) or '-'}", "",
             "| Dataset | Kategorije | Redovi | SHA256 |", "|---|---|---:|---|"]
    for d in datasets:
        lines.append(f"| {d['name']} | {', '.join(d['categories'])} | {d['rows']} | `{d['sha256'][:16]}` |")
    lines += ["", "## Napomene", "- Bez LUMI GPU za obradu podataka.", "- Bez objave na HF.", "- Gapovi nisu popunjeni nekvalitetnim podacima."]
    (out / "DATASET_CARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "version": version, "out_dir": str(out), "total_rows": total,
            "covered_categories": sorted(covered), "gaps": gaps, "datasets": datasets, "errors": errors}
