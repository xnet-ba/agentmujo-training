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
    # safety i reasoning PRIJE function-calling: isti uzorci ne smiju curiti u dva dataseta
    {"name": "agentmujo-safety", "file": "safety_v0.2.jsonl",
     "categories": ["safety"]},
    {"name": "agentmujo-reasoning", "file": "thinking_v0.1.jsonl",
     "categories": ["reasoning"]},
    {"name": "agentmujo-function-calling", "file": "function_calling_v0.1.jsonl",
     "categories": ["function-calling", "tool-use-mcp"]},
    {"name": "agentmujo-agentic-tasks", "file": "agentic_terminal_v0.1.jsonl",
     "categories": ["agentic-tasks", "linux-terminal"]},
    {"name": "agentmujo-bosnian-knowledge", "file": "knowledge_wikipedia_bs_v0.2.jsonl",
     "categories": ["knowledge"], "source": "wikipedia-bs"},
    {"name": "agentmujo-coding", "file": "coding_repo_v0.2.jsonl",
     "categories": ["coding"], "source": "own"},
    {"name": "agentmujo-rag-memory", "file": "rag_wikipedia_bs_v0.2.jsonl",
     "categories": ["rag-memory"], "source": "wikipedia-bs"},
]
PREFERENCE_SPEC = {"name": "agentmujo-preference-dpo", "file": "dpo_v0.5.jsonl",
                   "categories": ["preference-dpo"]}


def _sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _row_hash(row: dict[str, Any]) -> str:
    if row.get("messages"):
        return sample_hash(row)
    import hashlib
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


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
            r = build_dataset(src, out / spec["name"], spec["name"], version,
                               source_id=str(spec.get("source") or "own"))
            man = json.loads((out / spec["name"] / "manifest.json").read_text(encoding="utf-8"))
            datasets.append({"name": spec["name"], "categories": spec["categories"],
                             "source": str(spec.get("source") or "own"),
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
    bench_src = repo / "benchmarks" / "agentic_eval_v0.1.jsonl"
    benchmarks: list[dict[str, Any]] = []
    benchmark_rows = 0
    if bench_src.exists():
        import shutil
        bdir = out / "benchmarks"
        bdir.mkdir(parents=True, exist_ok=True)
        bdst = bdir / bench_src.name
        shutil.copy2(bench_src, bdst)
        benchmark_rows = len(read_jsonl(bench_src))
        benchmarks.append({"name": "agentmujo-agentic-evaluation", "role": "evaluation",
                           "categories": ["agentic-evaluation"], "rows": benchmark_rows,
                           "sha256": _sha(bdst), "path": str(bdst), "held_out": True,
                           "license": "Apache-2.0"})
        covered.add("agentic-evaluation")
    else:
        errors.append(f"benchmark: nema {bench_src}")
    # CROSS_DATASET_DEDUP_V1: isti uzorak u dva dataseta -> zadrzi prvi, ukloni iz kasnijeg.
    seen: dict[str, str] = {}
    removed: list[dict[str, Any]] = []
    removed_total = 0
    for d in datasets:
        dp = out / d["name"] / "data.jsonl"
        if not dp.exists():
            continue
        rows = read_jsonl(dp)
        kept: list[dict[str, Any]] = []
        local_removed = 0
        for i, row in enumerate(rows, 1):
            h = _row_hash(row)
            if h in seen:
                local_removed += 1
                if len(removed) < 20:
                    removed.append({"hash": h, "first": seen[h], "removed_from": d["name"],
                                    "line": i, "id": row.get("id")})
                continue
            seen[h] = d["name"]
            kept.append(row)
        if local_removed:
            write_jsonl(dp, kept)
            man = json.loads(Path(d["manifest"]).read_text(encoding="utf-8"))
            man["counts"]["cross_duplicates_removed"] = local_removed
            man["counts"]["rows"] = len(kept)
            man["languages"] = distribution(kept, "language") or {"?": len(kept)}
            man["tasks"] = (distribution(kept, "task") if d.get("format") != "preference"
                            else {"preference-dpo": len(kept)})
            man["data_sha256"] = _sha(dp)
            Path(d["manifest"]).write_text(json.dumps(man, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            d["rows"] = len(kept)
            d["sha256"] = man["data_sha256"]
            d["counts"] = man["counts"]
            d["languages"] = man["languages"]
            d["tasks"] = man["tasks"]
        d["cross_duplicates_removed"] = local_removed
        removed_total += local_removed
    datasets = [d for d in datasets if int(d.get("rows") or 0) > 0]  # EMPTY_DATASET_DROP_V1
    keep = {d["name"] for d in datasets} | ({"benchmarks"} if benchmarks else set())
    import shutil
    for child in out.iterdir():
        if child.is_dir() and child.name not in keep:
            shutil.rmtree(child, ignore_errors=True)
    covered = set()
    for d in datasets:
        covered.update(d.get("categories") or [])
    if benchmarks:
        covered.add("agentic-evaluation")
    gaps = [c for c in ALL_CATEGORIES if c not in covered]
    total = sum(int(d.get("rows") or 0) for d in datasets)
    release = {
        "schema": "agentmujo.release.v0", "name": "AgentMujo Dataset", "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(), "repository": "xnet-ba/agentmujo-training",
        "datasets": datasets, "benchmarks": benchmarks, "benchmark_rows": benchmark_rows,
        "covered_categories": sorted(covered), "gaps": gaps,
        "total_rows": total, "duplicates_across_datasets": 0,
        "overlap_removed": removed_total, "overlap_examples": removed[:20],
        "gpu_used": False, "lumi_used": False,
        "notes": "Release iz kanonskih fajlova; gapovi nisu popunjeni izmišljenim podacima. "
                 "agentic-evaluation je held-out benchmark, ne trening.",
        "errors": errors,
    }
    (out / "RELEASE.json").write_text(json.dumps(release, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["---", "language:", "  - bs", "license: other",
             "task_categories:", "  - text-generation", f"pretty_name: AgentMujo Dataset v{version}", "---", "",
             f"# AgentMujo Dataset Card — v{version}", "", f"**Ukupno redova:** {total}",
             f"**Kategorije:** {', '.join(sorted(covered))}", f"**Gapovi:** {', '.join(gaps) or '-'}", "",
             "| Dataset | Kategorije | Redovi | SHA256 |", "|---|---|---:|---|"]
    for d in datasets:
        lines.append(f"| {d['name']} | {', '.join(d['categories'])} | {d['rows']} | `{d['sha256'][:16]}` |")
    if benchmarks:
        lines += ["", "## Benchmark (evaluation, held-out)", "| Benchmark | Kategorija | Zadaci | SHA256 |", "|---|---|---:|---|"]
        for b in benchmarks:
            lines.append(f"| {b['name']} | {', '.join(b['categories'])} | {b['rows']} | `{b['sha256'][:16]}` |")
    lines += ["", "## Licence", "- knowledge/RAG: CC BY-SA 4.0 (Wikipedia; attribution URL u metadata).",
              "- coding: Apache-2.0 (vlastiti repo kod).", "- benchmark: Apache-2.0 (held-out, nije trening).",
              "- preference/ostalo: interno/Apache-2.0 po evidenciji.",
              "", "## Napomene", "- Bez LUMI GPU za obradu podataka.", "- Gapovi nisu popunjeni nekvalitetnim podacima."]
    (out / "DATASET_CARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "version": version, "out_dir": str(out), "total_rows": total,
            "benchmark_rows": benchmark_rows, "covered_categories": sorted(covered), "gaps": gaps,
            "datasets": datasets, "benchmarks": benchmarks, "errors": errors}
