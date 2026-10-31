import json
from pathlib import Path

from agentmujo_training.datasets.factory import (
    build_dataset, clean_rows, export_dataset, ingest_file, read_jsonl, write_jsonl,
)


def sample(i=1, task="function-calling"):
    return {
        "id": f"amj-fc-{i:04d}", "version": "0.1.0", "language": "bs-ijekavica",
        "task": task, "difficulty": "easy",
        "messages": [
            {"role": "user", "content": f"Provjeri status nginx servisa (test {i})."},
            {"role": "assistant", "content": "Provjeravam.",
             "tool_calls": [{"name": "service_status", "arguments": {"service": "nginx"}}]},
        ],
        "metadata": {"source": "test", "quality_tier": "GOLD", "verification_status": "human-reviewed"},
    }


def test_clean_dedup_and_reject(tmp_path):
    rows = [sample(1), sample(2), dict(sample(2)), {"id": "bad"}]
    kept, rejected, duplicates = clean_rows(rows)
    assert len(kept) == 2  # sample 1 + sample 2 (identicne poruke = duplicate)
    assert len(duplicates) == 1
    assert len(rejected) == 1


def test_build_manifest(tmp_path):
    inp = tmp_path / "in.jsonl"
    write_jsonl(inp, [sample(1), sample(2)])
    r = build_dataset(inp, tmp_path / "out", "agentmujo-test", "0.1.0", source_id="own")
    assert r["ok"] and r["counts"]["rows"] == 2
    man = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert man["schema"] == "agentmujo.dataset.v0"
    assert man["counts"]["input"] == 2
    assert man["data_sha256"]


def test_ingest_own_and_limit(tmp_path):
    inp = tmp_path / "in.jsonl"
    write_jsonl(inp, [sample(1), sample(2), sample(3)])
    r = ingest_file("own", inp, tmp_path / "out.jsonl", limit=2)
    assert r["ok"] and r["kept"] == 2
    assert len(read_jsonl(tmp_path / "out.jsonl")) == 2


def test_ingest_pending_blocked(tmp_path):
    inp = tmp_path / "in.jsonl"
    write_jsonl(inp, [sample(1)])
    r = ingest_file("hf", inp, tmp_path / "out.jsonl")
    assert r["ok"] is False


def test_export_qwen(tmp_path):
    inp = tmp_path / "in.jsonl"
    write_jsonl(inp, [sample(1)])
    r = export_dataset(inp, tmp_path / "qwen.jsonl", "qwen")
    assert r["ok"] and r["format"] == "qwen-xml-v0"
    txt = (tmp_path / "qwen.jsonl").read_text()
    assert "<tool_call>" in txt and "service_status" in txt
