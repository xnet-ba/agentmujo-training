"""Registar: skenira job tragove + benchmark rezultate + Hub pinove
u jedan docs/REGISTRY.md (tablice lineagea i evala)."""
from __future__ import annotations

import json
from pathlib import Path


def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build(repo: Path) -> str:
    lines = ["# AgentMujo registar (generirano: `amj registry build`)", ""]
    lines.append("## Lineage adaptera")
    lines.append("")
    lines.append("| Job | Baza/adapter | Dataset | Loss | Status |")
    lines.append("|---|---|---|---|---|")
    for jdir in sorted((repo / "training" / "jobs").iterdir()):
        if not jdir.is_dir():
            continue
        meta = _load_json(jdir / "metadata.json")
        status = _load_json(jdir / "outputs" / "status.json")
        metrics = _load_json(jdir / "outputs" / "metrics.json")
        if not meta and not status:
            continue
        base = (meta.get("base_model") or "?").split("/")[-1]
        if (jdir / "config.yaml").exists():
            import re
            cfg = (jdir / "config.yaml").read_text()
            m = re.search(r"base_adapter:\s*(\S+)", cfg)
            if m:
                base = "adapter: ..." + m.group(1)[-40:]
        loss = metrics.get("train_loss_mean", metrics.get("train_loss", "-"))
        if isinstance(loss, float):
            loss = round(loss, 3)
        lines.append(f"| {jdir.name} | {base} | {(meta.get('dataset') or '?').split('/')[-1]} "
                     f"| {loss} | {status.get('status', meta.get('status', '?'))} |")
    lines += ["", "## Benchmark izvještaji", "",
              "| Fajl | Profil | Ključne metrike |",
              "|---|---|---|"]
    for f in sorted((repo / "benchmark").glob("results_*.json")):
        d = _load_json(f)
        s = d.get("summary", {})
        def g(k):
            v = s.get(k, {})
            return v.get("mean", "-") if isinstance(v, dict) else "-"
        lines.append(f"| {f.name} | {d.get('profile', '?')} "
                     f"| tool={g('tool_selection')} arg={g('argument_accuracy')} "
                     f"safe={g('safety')} task={g('task_success')} |")
    lines += ["", "## Hub pinovi (configs/models.yaml, datasets.yaml)", "",
              "Dataset i model revizije su pinovane u configima; "
              "ovaj fajl se regenerira nakon svakog runa.", ""]
    return "\n".join(lines)
