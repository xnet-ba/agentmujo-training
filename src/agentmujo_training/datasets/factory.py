"""Dataset Factory core: ingest, clean, dedup, build/manifest, export."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .sources import load_sources
from .validator import sample_hash

SCHEMA_VERSION = "agentmujo.dataset.v0"
REQUIRED_SAMPLE = ("id", "version", "language", "task", "messages", "metadata")
EXPORT_FORMATS = {"openai", "canonical", "qwen"}


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            raise ValueError(f"{path}:{n}: nije validan JSON")
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{n}: zapis nije objekat")
        rows.append(row)
    return rows


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
                 encoding="utf-8")
    return len(rows)


def _sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _valid(row: dict[str, Any]) -> tuple[bool, str]:
    for f in REQUIRED_SAMPLE:
        if f not in row or row.get(f) in (None, "", []):
            return False, f"nedostaje polje: {f}"
    msgs = row.get("messages")
    if not isinstance(msgs, list) or len(msgs) < 2:
        return False, "premali broj poruka (min 2)"
    roles = []
    for m in msgs:
        if not isinstance(m, dict) or "role" not in m or "content" not in m:
            return False, "poruka nema role/content"
        roles.append(m.get("role"))
    if roles and roles[0] == "system":
        roles = roles[1:]
    if not roles or roles[0] != "user":
        return False, "konverzacija mora početi user porukom"
    if "assistant" not in roles:
        return False, "nedostaje assistant poruka"
    return True, ""


def clean_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, row in enumerate(rows, 1):
        ok, reason = _valid(row)
        if not ok:
            rejected.append({"line": i, "id": row.get("id"), "reason": reason})
            continue
        h = sample_hash(row)
        if h in seen:
            duplicates.append({"line": i, "id": row.get("id")})
            continue
        seen.add(h)
        kept.append(row)
    return kept, rejected, duplicates


def distribution(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        k = str(r.get(field) or "?")
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def _source_meta(source_id: str) -> tuple[str, str]:
    for s in load_sources(Path(__file__).resolve().parents[3]):
        if s.get("id") == source_id:
            return str(s.get("id")), str(s.get("license") or "")
    return source_id, ""


def ingest_file(source_id: str, input_path: str | Path, output_path: str | Path,
                limit: int = 0) -> dict[str, Any]:
    repo = Path(__file__).resolve().parents[3]
    src = next((s for s in load_sources(repo) if s.get("id") == source_id), None)
    if src is None:
        return {"ok": False, "err": f"nepoznat izvor '{source_id}'"}
    if str(src.get("status")) != "approved":
        return {"ok": False, "err": f"izvor '{source_id}' nije approved (status={src.get('status')})"}
    rows = read_jsonl(input_path)
    if limit and limit > 0:
        rows = rows[:limit]
    kept, rejected, duplicates = clean_rows(rows)
    write_jsonl(output_path, kept)
    return {"ok": True, "source": source_id, "license": src.get("license"),
            "input": str(input_path), "output": str(output_path), "input_rows": len(rows),
            "kept": len(kept), "rejected": len(rejected), "duplicates": len(duplicates),
            "languages": distribution(kept, "language"), "tasks": distribution(kept, "task")}


def clean_file(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    rows = read_jsonl(input_path)
    kept, rejected, duplicates = clean_rows(rows)
    write_jsonl(output_path, kept)
    return {"ok": True, "input": str(input_path), "output": str(output_path),
            "input_rows": len(rows), "kept": len(kept), "rejected": len(rejected),
            "duplicates": len(duplicates), "rejected_samples": rejected[:20]}


def deduplicate_file(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    r = clean_file(input_path, output_path)
    r["duplicates"] = r.get("duplicates", 0)
    return r


def build_dataset(input_path: str | Path, out_dir: str | Path, name: str, version: str,
                  source_id: str = "own") -> dict[str, Any]:
    rows = read_jsonl(input_path)
    kept, rejected, duplicates = clean_rows(rows)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data_path = out / "data.jsonl"
    write_jsonl(data_path, kept)
    sid, lic = _source_meta(source_id)
    manifest = {
        "schema": SCHEMA_VERSION, "name": name, "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": sid, "license": lic,
        "input": str(input_path), "data": str(data_path),
        "input_sha256": _sha(input_path), "data_sha256": _sha(data_path),
        "counts": {"input": len(rows), "kept": len(kept), "rejected": len(rejected),
                   "duplicates": len(duplicates), "rows": len(kept)},
        "languages": distribution(kept, "language"), "tasks": distribution(kept, "task"),
        "tiers": distribution([{"t": (r.get("metadata") or {}).get("quality_tier")} for r in kept], "t"),
        "rejected_samples": rejected[:20],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    return {"ok": True, "out_dir": str(out), "manifest": str(out / "manifest.json"),
            "counts": manifest["counts"], "languages": manifest["languages"], "tasks": manifest["tasks"]}


def export_dataset(input_path: str | Path, output_path: str | Path, fmt: str = "canonical") -> dict[str, Any]:
    fmt = str(fmt or "canonical").lower()
    if fmt not in EXPORT_FORMATS:
        return {"ok": False, "err": f"nepoznat format '{fmt}' (dozvoljeno: {sorted(EXPORT_FORMATS)})"}
    rows = read_jsonl(input_path)
    out_rows: list[dict[str, Any]] = []
    for r in rows:
        if fmt != "qwen":
            out_rows.append(r)
            continue
        row = json.loads(json.dumps(r, ensure_ascii=False))
        for m in row.get("messages", []):
            if m.get("role") == "assistant" and m.get("tool_calls"):
                calls = []
                for tc in m.get("tool_calls") or []:
                    calls.append({"name": tc.get("name"), "arguments": tc.get("arguments") or {}})
                m["content"] = (str(m.get("content") or "") + "\n<tool_call>" +
                                json.dumps(calls, ensure_ascii=False) + "</tool_call>").strip()
                m.pop("tool_calls", None)
        out_rows.append(row)
    write_jsonl(output_path, out_rows)
    return {"ok": True, "format": ("qwen-xml-v0" if fmt == "qwen" else fmt), "input": str(input_path),
            "output": str(output_path), "rows": len(out_rows), "output_sha256": _sha(output_path)}
